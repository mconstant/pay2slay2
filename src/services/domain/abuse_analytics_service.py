from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AbuseStats:
    by_region: dict[str, int]


class AbuseAnalyticsService:
    def capture_region_kill(self, region: str, kills: int = 1) -> None:
        # TODO: wire to a metrics backend or table; stubbed no-op
        _ = (region, kills)
