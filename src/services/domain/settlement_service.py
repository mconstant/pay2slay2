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
        """Derive payable subset of kills honoring daily/weekly kill caps.

        Caps count total kills paid out (via sent payouts), not number of payouts.
        If the user has already been paid for >= daily_cap kills today, zero out.
        Otherwise, clamp the payable kills to the remaining allowance and scale BAN
        proportionally.
        """
        now = datetime.now(UTC)
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        from ...models.models import Payout

        # Sum of kills already paid (via sent payouts) in the daily window.
        # Each accrual row linked to a sent payout records the kills it covered.
        day_kills_paid = (
            self.session.query(func.coalesce(func.sum(RewardAccrual.kills), 0))
            .join(Payout, RewardAccrual.payout_id == Payout.id)
            .filter(
                RewardAccrual.user_id == candidate.user.id,
                Payout.status == "sent",
                Payout.created_at >= day_ago,
            )
            .scalar()
        ) or 0

        week_kills_paid = (
            self.session.query(func.coalesce(func.sum(RewardAccrual.kills), 0))
            .join(Payout, RewardAccrual.payout_id == Payout.id)
            .filter(
                RewardAccrual.user_id == candidate.user.id,
                Payout.status == "sent",
                Payout.created_at >= week_ago,
            )
            .scalar()
        ) or 0

        remaining_daily = max(self.daily_cap - day_kills_paid, 0)
        remaining_weekly = max(self.weekly_cap - week_kills_paid, 0)
        allowed_kills = min(remaining_daily, remaining_weekly, candidate.total_kills)

        if allowed_kills <= 0:
            return SettlementCandidate(
                user=candidate.user,
                total_kills=candidate.total_kills,
                total_amount_ban=candidate.total_amount_ban,
                payable_kills=0,
                payable_amount_ban=Decimal("0"),
            )

        # Scale BAN proportionally if capped below total
        if allowed_kills < candidate.total_kills and candidate.total_kills > 0:
            ratio = Decimal(str(allowed_kills)) / Decimal(str(candidate.total_kills))
            payable_ban = (candidate.total_amount_ban * ratio).quantize(Decimal("0.00000001"))
        else:
            payable_ban = candidate.total_amount_ban

        return SettlementCandidate(
            user=candidate.user,
            total_kills=candidate.total_kills,
            total_amount_ban=candidate.total_amount_ban,
            payable_kills=allowed_kills,
            payable_amount_ban=payable_ban,
        )
