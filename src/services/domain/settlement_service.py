from __future__ import annotations

import random
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...models.models import RewardAccrual, User


@dataclass
class SettlementCandidate:
    user: User
    total_kills: int
    total_amount_ban: float


class SettlementService:
    def __init__(self, session: Session, daily_cap: int, weekly_cap: int) -> None:
        self.session = session
        self.daily_cap = daily_cap
        self.weekly_cap = weekly_cap

    def select_candidates(self, limit: int | None = None) -> list[SettlementCandidate]:
        # Simplified: group unsettled accruals per user
        q = (
            select(RewardAccrual.user_id, func.sum(RewardAccrual.kills), func.sum(RewardAccrual.amount_ban))
            .where(RewardAccrual.settled == False)  # noqa: E712
            .group_by(RewardAccrual.user_id)
        )
        if limit:
            q = q.limit(limit)
        rows = self.session.execute(q).all()
        candidates: list[SettlementCandidate] = []
        for user_id, kills_sum, amt_sum in rows:
            user = self.session.get(User, user_id)
            if not user:
                continue
            candidates.append(
                SettlementCandidate(user=user, total_kills=int(kills_sum or 0), total_amount_ban=float(amt_sum or 0.0))
            )
        random.shuffle(candidates)
        return candidates

    def apply_caps(self, candidate: SettlementCandidate) -> SettlementCandidate:
        # Placeholder: in real impl, compute prior payouts in 24h/7d windows
        return candidate
