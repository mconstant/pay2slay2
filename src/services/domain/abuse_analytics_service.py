from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from prometheus_client import Counter
from sqlalchemy.orm import Session


@dataclass
class AbuseStats:
    by_region: dict[str, int]


KILLS_BY_REGION = Counter(
    "kills_by_region_total",
    "Total kills accrued tagged by region header",
    labelnames=["region"],
)

PAYOUTS_BY_REGION = Counter(
    "payouts_by_region_total",
    "Total payouts created by user region",
    labelnames=["region"],
)

FLAGGED_USERS_TOTAL = Counter(
    "flagged_users_total",
    "Total users flagged by abuse heuristics (placeholder)",
)


class AbuseAnalyticsService:
    def __init__(
        self, session: Session | None = None, kill_rate_threshold: int | None = None
    ) -> None:
        self.session = session
        self.kill_rate_threshold = kill_rate_threshold or 0

    def capture_region_kill(self, region: str | None, kills: int = 1) -> None:
        region = region or "unknown"
        KILLS_BY_REGION.labels(region=region).inc(kills)

    def record_payout(self, region: str | None) -> None:
        region = region or "unknown"
        PAYOUTS_BY_REGION.labels(region=region).inc()

    def flag_user(self) -> None:
        FLAGGED_USERS_TOTAL.inc()

    def evaluate_kill_spike(self, user_id: int, recent_window_min: int = 15) -> bool:
        """Return True and persist AbuseFlag if user kill volume in window exceeds threshold.

        Disabled if session absent or threshold is 0.
        """
        if not self.session or not self.kill_rate_threshold:
            return False
        from src.models.models import AbuseFlag, RewardAccrual

        cutoff = datetime.utcnow() - timedelta(minutes=recent_window_min)
        q = self.session.query(RewardAccrual.kills).filter(
            RewardAccrual.user_id == user_id, RewardAccrual.created_at >= cutoff
        )
        rows = q.all()
        total_recent = sum((r[0] or 0) for r in rows)
        if total_recent > self.kill_rate_threshold:
            self.session.add(
                AbuseFlag(
                    user_id=user_id,
                    flag_type="kill_rate_spike",
                    severity="med",
                    detail=f"kills={total_recent} window_min={recent_window_min}",
                )
            )
            self.flag_user()
            return True
        return False


__all__ = [
    "AbuseAnalyticsService",
    "AbuseStats",
    "KILLS_BY_REGION",
    "PAYOUTS_BY_REGION",
    "FLAGGED_USERS_TOTAL",
]
