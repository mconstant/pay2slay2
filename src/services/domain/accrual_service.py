from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from math import floor

from sqlalchemy.orm import Session

from ...models.models import RewardAccrual, User
from ..fortnite_service import FortniteService


@dataclass
class AccrualResult:
    user_id: int
    kills_delta: int
    amount_ban: float
    epoch_minute: int
    created: bool


class AccrualService:
    """Compute kill deltas per user and persist RewardAccrual rows.

    NOTE: FortniteService is currently a stub; real implementation will return deltas or absolute kills.
    We treat user.last_settled_kill_count as a cursor for unpaid kills. We DO NOT advance it here; only
    settlement will advance that cursor after payouts are created to maintain idempotency across crashes.
    """

    def __init__(
        self, session: Session, fortnite: FortniteService, payout_amount_per_kill: float
    ) -> None:
        self.session = session
        self.fortnite = fortnite
        self.payout_amount_per_kill = payout_amount_per_kill

    def accrue_for_user(self, user: User, now: datetime | None = None) -> AccrualResult | None:
        if not user.epic_account_id:
            return None
        # Placeholder delta until Fortnite integration: 0 (no accrual). Future: fetch via fortnite.get_kills_since(...)
        delta_kills = 0
        if delta_kills <= 0:
            return AccrualResult(
                user_id=user.id,
                kills_delta=0,
                amount_ban=0.0,
                epoch_minute=0,
                created=False,
            )
        ts = now or datetime.now(UTC)
        epoch_minute = floor(ts.timestamp() / 60)
        amount = delta_kills * self.payout_amount_per_kill
        existing = (
            self.session.query(RewardAccrual)
            .filter(RewardAccrual.user_id == user.id, RewardAccrual.epoch_minute == epoch_minute)
            .one_or_none()
        )
        if existing:
            return AccrualResult(
                user_id=user.id,
                kills_delta=0,
                amount_ban=float(existing.amount_ban),
                epoch_minute=epoch_minute,
                created=False,
            )
        accrual = RewardAccrual(
            user_id=user.id,
            kills=delta_kills,
            amount_ban=amount,
            epoch_minute=epoch_minute,
            settled=False,
        )
        self.session.add(accrual)
        return AccrualResult(
            user_id=user.id,
            kills_delta=delta_kills,
            amount_ban=amount,
            epoch_minute=epoch_minute,
            created=True,
        )
