from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ...models.models import RewardAccrual, User


@dataclass
class AccrualResult:
    user_id: int
    kills: int
    amount_ban: float
    epoch_minute: int


class AccrualService:
    def __init__(self, session: Session, payout_per_kill_ban: float) -> None:
        self.session = session
        self.payout_per_kill_ban = payout_per_kill_ban

    def record_kills(self, user: User, kills: int, epoch_minute: int | None = None) -> AccrualResult:
        if kills <= 0:
            return AccrualResult(user_id=user.id, kills=0, amount_ban=0.0, epoch_minute=epoch_minute or 0)
        minute = epoch_minute or int(datetime.now(UTC).timestamp() // 60)
        amount = float(kills) * float(self.payout_per_kill_ban)
        accrual = RewardAccrual(user_id=user.id, kills=kills, amount_ban=amount, epoch_minute=minute)
        self.session.add(accrual)
        return AccrualResult(user_id=user.id, kills=kills, amount_ban=amount, epoch_minute=minute)
