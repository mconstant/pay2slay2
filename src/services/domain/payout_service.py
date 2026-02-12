from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models.models import Payout, RewardAccrual, User, WalletLink
from ..banano_client import BananoClient, seed_to_address

# Module-level metrics (registered once to avoid duplication errors)
_payout_amount_hist = Histogram(
    "payout_amount_ban",
    "Distribution of payout amounts (BAN)",
    buckets=(0.0001, 0.001, 0.01, 0.1, 1.0, 5.0, 10.0, 25.0, 50.0),
)
_accrual_lag_gauge = Gauge(
    "payout_accrual_lag_minutes",
    "Minutes between oldest unsettled accrual and payout creation",
)
_attempts_counter = Counter("payout_attempts_total", "Total payout send attempts", ["result"])
_retry_latency_hist = Histogram(
    "payout_retry_latency_seconds", "Delay between payout retry attempts"
)


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
        # Use module-level metrics (T066)
        self._payout_amount_hist = _payout_amount_hist
        self._accrual_lag_gauge = _accrual_lag_gauge

    def _get_primary_address(self, user: User) -> str | None:
        q = select(WalletLink).where(WalletLink.user_id == user.id, WalletLink.is_primary == True)  # noqa: E712
        row = self.session.execute(q).scalars().first()
        return row.address if row else None

    def create_payout(  # noqa: PLR0915 - complex orchestration kept inline for traceability
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
        # Metrics capture (T066)
        try:
            self._payout_amount_hist.observe(float(amount_ban))
            if accruals:
                oldest = min(a.created_at for a in accruals if getattr(a, "created_at", None))
                if oldest:
                    lag_min = max((now - oldest).total_seconds() / 60.0, 0.0)
                    self._accrual_lag_gauge.set(lag_min)
        except Exception:
            pass
        import random
        import time

        def _attempt_send() -> bool:
            if self.dry_run:
                payout.tx_hash = "dryrun"
                payout.status = "sent"
                return True
            # T065: Preflight operator balance minimal check (if implemented upstream)
            try:
                if not self.banano.has_min_balance(
                    float(amount_ban) * 1.1,  # 10% margin
                    operator_account=self.banano._seed
                    and seed_to_address(self.banano._seed)
                    or None,
                ):
                    payout.status = "failed"
                    payout.error_detail = "Insufficient operator balance"
                    return False
            except Exception:
                pass
            amount_raw = self.banano.ban_to_raw(amount_ban)
            try:
                tx = self.banano.send(
                    source_wallet="operator", to_address=address, amount_raw=amount_raw
                )
            except Exception as send_exc:
                payout.status = "failed"
                payout.error_detail = str(send_exc)[:500]
                return False
            payout.tx_hash = tx
            payout.status = "sent" if tx else "failed"
            if not tx:
                payout.error_detail = "send returned no tx hash"
            return payout.status == "sent"

        success = _attempt_send()
        attempt = 1
        while not success and attempt <= max_retries:
            attempt += 1
            payout.attempt_count = attempt
            payout.last_attempt_at = datetime.now(UTC)
            # jittered exponential backoff (capped small since scheduler loop handles broader timing)
            sleep_for = min(backoff_base * (2 ** (attempt - 1)) * (0.5 + random.random()), 5.0)
            _retry_latency_hist.observe(sleep_for)
            time.sleep(sleep_for)
            success = _attempt_send()
        _attempts_counter.labels(result="success" if success else "failed").inc()
        # Cursor is now advanced during accrual (not here) to prevent duplicate counting.
        if payout.status == "sent":
            user.last_settlement_at = datetime.now(UTC)
        return PayoutResult(
            user_id=user.id,
            payout_id=0,
            amount_ban=amount_ban,
            tx_hash=payout.tx_hash,
            status=payout.status,
        )
