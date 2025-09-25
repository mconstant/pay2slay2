from __future__ import annotations

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

    def create_payout(self, user: User, amount_ban: float, accruals: list[RewardAccrual]) -> PayoutResult | None:
        address = self._get_primary_address(user)
        if not address:
            return None
        payout = Payout(user_id=user.id, address=address, amount_ban=amount_ban, status="pending")
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
            tx = self.banano.send(source_wallet="operator", to_address=address, amount_raw=str(amount_ban))
            payout.tx_hash = tx
            payout.status = "sent" if tx else "failed"
        return PayoutResult(user_id=user.id, payout_id=0, amount_ban=amount_ban, tx_hash=payout.tx_hash, status=payout.status)
