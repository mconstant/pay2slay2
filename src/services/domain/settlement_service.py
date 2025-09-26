from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...models.models import RewardAccrual, User


@dataclass
class SettlementCandidate:
    user: User
    total_kills: int  # kills represented by unsettled accrual rows
    total_amount_ban: Decimal
    payable_kills: int | None = None  # after caps
    payable_amount_ban: Decimal | None = None


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
                    total_amount_ban=Decimal(str(amt_sum or 0)),
                )
            )
        random.shuffle(candidates)
        return [self.apply_caps(c) for c in candidates]

    def apply_caps(self, candidate: SettlementCandidate) -> SettlementCandidate:
        """Derive payable subset of kills honoring daily/weekly payout count caps.

        Current policy: caps count payouts, not kills. If caps exceeded -> no payout.
        If remaining daily or weekly allowance is 0, zero out. Otherwise full candidate is payable.
        (Future: support per-kill monetary caps; partial payment logic would adjust counts.)
        """
        now = datetime.now(UTC)
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
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
        remaining_daily = max(self.daily_cap - day_count, 0)
        remaining_weekly = max(self.weekly_cap - week_count, 0)
        if remaining_daily <= 0 or remaining_weekly <= 0:
            return SettlementCandidate(
                user=candidate.user,
                total_kills=candidate.total_kills,
                total_amount_ban=candidate.total_amount_ban,
                payable_kills=0,
                payable_amount_ban=Decimal("0"),
            )
        # For now, either full amount or zero (no partial monetary cap). Keep fields explicit.
        return SettlementCandidate(
            user=candidate.user,
            total_kills=candidate.total_kills,
            total_amount_ban=candidate.total_amount_ban,
            payable_kills=candidate.total_kills,
            payable_amount_ban=candidate.total_amount_ban,
        )
