from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

import httpx

HTTP_OK = 200


@dataclass
class KillsDelta:
    epic_account_id: str
    since_cursor: str | None
    new_cursor: str | None
    kills: int


class FortniteService:
    """Fortnite API integration (simplified).

    Current implementation assumes there is an endpoint that returns a cumulative kill count
    for the player (e.g., lifetime kills in a mode). We transform that into a delta using the
    provided cursor (previous settled kill count as string). If the API call fails, we return
    zero delta so accrual logic remains idempotent and resilient.

    Rate limiting: simple token bucket replenished every second based on per-minute quota.
    Thread-safe for basic multi-threaded scheduler usage.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://fortnite.example.api/v1",
        per_minute_limit: int = 60,
        client_factory: Callable[[], httpx.Client] | None = None,
        dry_run: bool = True,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.per_minute_limit = max(per_minute_limit, 1)
        self._tokens = self.per_minute_limit
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()
        self._client_factory = client_factory or (lambda: httpx.Client(timeout=5.0))
        self._dry_run = dry_run

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
            self._refill()
            if self._tokens > 0:
                self._tokens -= 1
                return True
            return False

    # --- Public API ---
    def get_kills_since(self, epic_account_id: str, cursor: str | None) -> KillsDelta:
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
            return KillsDelta(
                epic_account_id=epic_account_id,
                since_cursor=cursor,
                new_cursor=cursor,
                kills=0,
            )

        # Perform request
        try:
            with self._client_factory() as client:
                resp = client.get(
                    f"{self.base_url}/players/{epic_account_id}/stats",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if resp.status_code != HTTP_OK:
                    return KillsDelta(
                        epic_account_id=epic_account_id,
                        since_cursor=cursor,
                        new_cursor=cursor,
                        kills=0,
                    )
                data = resp.json()
                # Expecting JSON like {"lifetime_kills": 1234}
                lifetime_kills = int(data.get("lifetime_kills", 0))
        except Exception:
            lifetime_kills = int(cursor) if cursor and cursor.isdigit() else 0

        prev = int(cursor) if cursor and cursor.isdigit() else 0
        delta = lifetime_kills - prev
        # Guard against reset / mode switch: ignore negative jump
        delta = max(delta, 0)
        return KillsDelta(
            epic_account_id=epic_account_id,
            since_cursor=cursor,
            new_cursor=str(lifetime_kills),
            kills=delta,
        )
