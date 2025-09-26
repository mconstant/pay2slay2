from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from prometheus_client import Counter, Histogram
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models.models import Payout, RewardAccrual, User, WalletLink
from ..banano_client import BananoClient


@dataclass
class PayoutResult:
    user_id: int
    payout_id: int
    amount_ban: Decimal
    tx_hash: str | None
    status: str


class PayoutService:
    def __init__(self, session: Session, banano: BananoClient, dry_run: bool = True) -> None:
        self.session = session
        self.dry_run = dry_run
        self.banano = banano

    def _get_primary_address(self, user: User) -> str | None:
        q = select(WalletLink).where(WalletLink.user_id == user.id, WalletLink.is_primary == True)  # noqa: E712
        row = self.session.execute(q).scalars().first()
        return row.address if row else None

    def create_payout(
        self,
        user: User,
        amount_ban: Decimal,
        accruals: list[RewardAccrual],
        max_retries: int = 2,
        backoff_base: float = 0.5,
    ) -> PayoutResult | None:
        address = self._get_primary_address(user)
        if not address:
            return None
        # Idempotency: hash sorted accrual IDs; if existing payout with same hash & sent, short-circuit
        accrual_ids = sorted(a.id for a in accruals)
        raw_key = ",".join(str(i) for i in accrual_ids).encode("utf-8")
        idem_key = hashlib.sha256(raw_key).hexdigest()
        existing = (
            self.session.query(Payout)
            .filter(Payout.user_id == user.id, Payout.idempotency_key == idem_key)
            .one_or_none()
        )
        if existing and existing.status == "sent":
            return PayoutResult(
                user_id=user.id,
                payout_id=existing.id,
                amount_ban=Decimal(existing.amount_ban),
                tx_hash=existing.tx_hash,
                status=existing.status,
            )
        now = datetime.now(UTC)
        payout = Payout(
            user_id=user.id,
            address=address,
            amount_ban=amount_ban,
            status="pending",
            first_attempt_at=now,
            last_attempt_at=now,
            idempotency_key=idem_key,
        )
        self.session.add(payout)
        # Mark accruals as settled and link to payout
        for a in accruals:
            a.settled = True
            a.settled_at = datetime.now(UTC)
            a.payout = payout
        import random
        import time

        def _attempt_send() -> bool:
            if self.dry_run:
                payout.tx_hash = "dryrun"
                payout.status = "sent"
                return True
            tx = self.banano.send(
                source_wallet="operator", to_address=address, amount_raw=str(amount_ban)
            )
            payout.tx_hash = tx
            payout.status = "sent" if tx else "failed"
            return payout.status == "sent"

        attempts_counter = Counter(
            "payout_attempts_total", "Total payout send attempts", ["result"]
        )
        retry_latency_hist = Histogram(
            "payout_retry_latency_seconds", "Delay between payout retry attempts"
        )
        success = _attempt_send()
        attempt = 1
        while not success and attempt <= max_retries:
            attempt += 1
            payout.attempt_count = attempt
            payout.last_attempt_at = datetime.now(UTC)
            # jittered exponential backoff (capped small since scheduler loop handles broader timing)
            sleep_for = min(backoff_base * (2 ** (attempt - 1)) * (0.5 + random.random()), 5.0)
            retry_latency_hist.observe(sleep_for)
            time.sleep(sleep_for)
            success = _attempt_send()
        attempts_counter.labels(result="success" if success else "failed").inc()
        # Advance cursor if payout succeeded (sum accrual kills added to cursor)
        if payout.status == "sent":
            total_kills = sum(a.kills for a in accruals)
            user.last_settled_kill_count += total_kills
            user.last_settlement_at = datetime.now(UTC)
        return PayoutResult(
            user_id=user.id,
            payout_id=0,
            amount_ban=amount_ban,
            tx_hash=payout.tx_hash,
            status=payout.status,
        )
