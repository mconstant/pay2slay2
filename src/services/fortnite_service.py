from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from random import random
from typing import Any

import httpx
from prometheus_client import Counter, Histogram

from src.lib.observability import instrument_http_call

HTTP_OK = 200


@dataclass
class KillsDelta:
    epic_account_id: str
    since_cursor: str | None
    new_cursor: str | None
    kills: int


# Metrics (module-level; cheap counters)
FORTNITE_CALLS = Counter("fortnite_calls_total", "Total Fortnite API calls attempted")
FORTNITE_ERRORS = Counter("fortnite_errors_total", "Fortnite API call errors")
FORTNITE_RATE_LIMITED = Counter(
    "fortnite_local_rate_limited_total", "Local rate limit short-circuited calls"
)
FORTNITE_KILLS_DELTA = Counter("fortnite_kills_delta_total", "Observed kill delta (post-guard)")
FORTNITE_LATENCY = Histogram("fortnite_request_latency_seconds", "Latency of Fortnite API requests")

_ADAPTIVE_MIN_LIMIT = 10
_ADAPTIVE_MAX_LIMIT = 600


class FortniteService:
    """Fortnite API integration (simplified).

    Current implementation assumes there is an endpoint that returns a cumulative kill count
    for the player (e.g., lifetime kills in a mode). We transform that into a delta using the
    provided cursor (previous settled kill count as string). If the API call fails, we return
    zero delta so accrual logic remains idempotent and resilient.

    Rate limiting: simple token bucket replenished every second based on per-minute quota.
    Thread-safe for basic multi-threaded scheduler usage.
    """

    def __init__(  # noqa: PLR0913 - parameter count acceptable for config object
        self,
        api_key: str,
        base_url: str = "https://fortnite.example.api/v1",
        per_minute_limit: int = 60,
        client_factory: Callable[[], httpx.Client] | None = None,
        dry_run: bool = True,
        max_retries: int = 2,
        backoff_base: float = 0.25,
        auth_header_name: str = "Authorization",
        auth_scheme: str = "",
        concurrency_limit: int = 4,
        adaptive: bool = True,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.per_minute_limit = max(per_minute_limit, 1)
        self._tokens = self.per_minute_limit
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()
        self._client_factory = client_factory or (lambda: httpx.Client(timeout=5.0))
        self._dry_run = dry_run
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._auth_header_name = auth_header_name
        self._auth_scheme = auth_scheme
        self._adaptive = adaptive
        self._concurrency_limit = max(concurrency_limit, 1)
        self._in_flight = 0

    # --- Rate limiting helpers ---
    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed <= 0:
            return
        # Refill proportionally up to capacity
        per_second = self.per_minute_limit / 60.0
        new_tokens = int(elapsed * per_second)
        if new_tokens > 0:
            self._tokens = min(self.per_minute_limit, self._tokens + new_tokens)
            self._last_refill = now

    def _acquire(self) -> bool:
        with self._lock:
            # Concurrency gate first
            if self._in_flight >= self._concurrency_limit:
                return False
            self._refill()
            if self._tokens > 0:
                self._tokens -= 1
                self._in_flight += 1
                return True
            return False

    def _release(self) -> None:
        with self._lock:
            if self._in_flight > 0:
                self._in_flight -= 1

    # --- Public API ---
    def get_kills_since(  # noqa: PLR0912 - acceptable branch count for retry & adaptation
        self, epic_account_id: str, cursor: str | None
    ) -> KillsDelta:
        # Dry-run: simulate zero change (future: optionally randomize)
        if self._dry_run:
            curr_total = int(cursor) if cursor and cursor.isdigit() else 0
            return KillsDelta(
                epic_account_id=epic_account_id,
                since_cursor=cursor,
                new_cursor=str(curr_total),
                kills=0,
            )

        if not self._acquire():
            # Rate limit exceeded locally; treat as no-op delta
            FORTNITE_RATE_LIMITED.inc()
            return KillsDelta(
                epic_account_id=epic_account_id,
                since_cursor=cursor,
                new_cursor=cursor,
                kills=0,
            )
        lifetime_kills: int
        FORTNITE_CALLS.inc()
        for attempt in range(self._max_retries + 1):
            start = time.monotonic()
            try:
                with self._client_factory() as client:
                    scheme_prefix = f"{self._auth_scheme} " if self._auth_scheme else ""
                    headers = {self._auth_header_name: f"{scheme_prefix}{self.api_key}"}
                    url = f"{self.base_url}/stats/br/v2/{epic_account_id}"

                    def _do(
                        url: str = url,
                        headers: dict[str, str] = headers,
                        client: httpx.Client = client,
                    ) -> httpx.Response:
                        return client.get(url, headers=headers)

                    resp = instrument_http_call(
                        "fortnite.get_player_stats",
                        _do,
                        attrs={
                            "http.url": url,
                            "http.method": "GET",
                            "service.component": "fortnite",
                            "epic.account_id": epic_account_id,
                        },
                    )
                    FORTNITE_LATENCY.observe(time.monotonic() - start)
                    if resp.status_code == HTTP_OK:
                        data: dict[str, Any] = resp.json()
                        # fortnite-api.com nests kills at data.stats.all.overall.kills
                        stats = data.get("data", {}).get("stats", {})
                        overall = stats.get("all", {}).get("overall", {})
                        lifetime_kills = int(overall.get("kills", 0))
                        break
                    # non-200 triggers retry
            except Exception:  # pragma: no cover - network variability
                FORTNITE_LATENCY.observe(time.monotonic() - start)
                # swallow and retry
            # Backoff if not last attempt
            if attempt < self._max_retries:
                # jittered exponential backoff
                sleep_for = self._backoff_base * (2**attempt) * (0.5 + random())
                time.sleep(min(sleep_for, 2.0))
        else:  # exhausted
            FORTNITE_ERRORS.inc()
            lifetime_kills = int(cursor) if cursor and cursor.isdigit() else 0
        # Adaptive tuning: if many calls produce zero delta consecutively, shrink limit; if positive deltas and spare capacity, gently increase
        try:  # pragma: no cover - heuristic
            if lifetime_kills == (int(cursor) if cursor and cursor.isdigit() else 0):
                # no change
                with self._lock:
                    if self._adaptive and self.per_minute_limit > _ADAPTIVE_MIN_LIMIT:
                        self.per_minute_limit = max(
                            int(self.per_minute_limit * 0.95), _ADAPTIVE_MIN_LIMIT
                        )
            else:
                with self._lock:
                    if self._adaptive and self.per_minute_limit < _ADAPTIVE_MAX_LIMIT:
                        self.per_minute_limit = min(
                            int(self.per_minute_limit * 1.05) + 1, _ADAPTIVE_MAX_LIMIT
                        )
        except Exception:
            pass
        finally:
            self._release()

        prev = int(cursor) if cursor and cursor.isdigit() else 0
        delta = lifetime_kills - prev
        # Guard against reset / mode switch: ignore negative jump
        delta = max(delta, 0)
        if delta > 0:
            FORTNITE_KILLS_DELTA.inc(delta)
        return KillsDelta(
            epic_account_id=epic_account_id,
            since_cursor=cursor,
            new_cursor=str(lifetime_kills),
            kills=delta,
        )


def seed_kill_baseline(fortnite: FortniteService, epic_account_id: str) -> int:
    """Fetch current lifetime kills to use as the starting cursor for a newly linked user.

    Called when epic_account_id is first set (or changes) so only kills earned
    after linking generate payouts.  Returns the baseline kill count.
    """
    result = fortnite.get_kills_since(epic_account_id, "0")
    return int(result.new_cursor) if result.new_cursor else 0
