from __future__ import annotations

from dataclasses import dataclass

from prometheus_client import Counter


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
    def capture_region_kill(self, region: str | None, kills: int = 1) -> None:
        if not region:
            region = "unknown"
        KILLS_BY_REGION.labels(region=region).inc(kills)

    def record_payout(self, region: str | None) -> None:
        if not region:
            region = "unknown"
        PAYOUTS_BY_REGION.labels(region=region).inc()

    def flag_user(self) -> None:
        FLAGGED_USERS_TOTAL.inc()


__all__ = [
    "AbuseAnalyticsService",
    "AbuseStats",
    "KILLS_BY_REGION",
    "PAYOUTS_BY_REGION",
    "FLAGGED_USERS_TOTAL",
]
