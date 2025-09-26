from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models.models import Payout, RewardAccrual, User, WalletLink
from ..banano_client import BananoClient


@dataclass
class PayoutResult:
    user_id: int
    payout_id: int
    amount_ban: float
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
        self, user: User, amount_ban: float, accruals: list[RewardAccrual]
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
                amount_ban=float(existing.amount_ban),
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
        if self.dry_run:
            payout.status = "sent"
            payout.tx_hash = "dryrun"
        else:
            # Convert BAN to raw if needed (placeholder: assume input already in BAN and node accepts it)
            tx = self.banano.send(
                source_wallet="operator", to_address=address, amount_raw=str(amount_ban)
            )
            payout.tx_hash = tx
            payout.status = "sent" if tx else "failed"
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
