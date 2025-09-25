from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

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
            select(
                RewardAccrual.user_id,
                func.sum(RewardAccrual.kills),
                func.sum(RewardAccrual.amount_ban),
            )
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
                SettlementCandidate(
                    user=user,
                    total_kills=int(kills_sum or 0),
                    total_amount_ban=float(amt_sum or 0.0),
                )
            )
        random.shuffle(candidates)
        return [self.apply_caps(c) for c in candidates]

    def apply_caps(self, candidate: SettlementCandidate) -> SettlementCandidate:
        # Compute payouts in last 24h and 7d to enforce caps
        now = datetime.now(UTC)
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        # Count payouts in windows
        from ...models.models import Payout

        day_count = (
            self.session.query(Payout)
            .filter(Payout.user_id == candidate.user.id, Payout.created_at >= day_ago)
            .count()
        )
        week_count = (
            self.session.query(Payout)
            .filter(Payout.user_id == candidate.user.id, Payout.created_at >= week_ago)
            .count()
        )
        # If over cap, zero out this candidate
        if day_count >= self.daily_cap or week_count >= self.weekly_cap:
            return SettlementCandidate(user=candidate.user, total_kills=0, total_amount_ban=0.0)
        return candidate
