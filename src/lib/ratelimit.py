from __future__ import annotations

import os
import threading
import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import Counter

from .observability import get_logger

log = get_logger("ratelimit")

# Prometheus metric: label 'scope' differentiates which limiter rejected
RATE_LIMIT_REJECTS = Counter(
    "http_rate_limited_total", "Requests rejected by rate limiter", ["scope"]
)


class TokenBucket:
    """Simple per-key token bucket (in-memory, process local).

    capacity: max tokens (also refill ceiling)
    refill_rate: tokens per second (float) added up to capacity
    state: dict[key] = (tokens, last_refill_mono)
    Thread-safe via a single lock; suitable for modest QPS.
    """

    def __init__(self, capacity: int, per_minute: int) -> None:
        per_minute = max(per_minute, 1)
        self.capacity = per_minute
        self.refill_rate = per_minute / 60.0
        self._lock = threading.Lock()
        self._state: dict[str, tuple[float, float]] = {}

    def _refill_unlocked(self, key: str, now: float) -> None:
        tokens, last = self._state.get(key, (self.capacity, now))
        if now > last:
            delta = now - last
            tokens = min(self.capacity, tokens + delta * self.refill_rate)
            last = now
        self._state[key] = (tokens, last)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            self._refill_unlocked(key, now)
            tokens, last = self._state[key]
            if tokens >= 1.0:
                self._state[key] = (tokens - 1.0, last)
                return True
            return False


def build_rate_limiters(
    config: Any | None,
) -> list[tuple[TokenBucket, Callable[[Request], str], str]]:
    """Build configured rate limiters from config + env overrides.

    Returns list of (bucket, key_func, scope_name).
    """

    limits_cfg = (
        getattr(getattr(config, "integrations", None), "rate_limits", {}) or {} if config else {}
    )

    # Env override helpers
    def _env_int(name: str, default: int) -> int:
        try:
            return int(os.getenv(name, str(default)))
        except Exception:  # pragma: no cover - defensive
            return default

    global_per_minute = _env_int(
        "RATE_LIMIT_GLOBAL_PER_MINUTE", limits_cfg.get("global_per_minute", 300)
    )
    per_ip_per_minute = _env_int(
        "RATE_LIMIT_PER_IP_PER_MINUTE", limits_cfg.get("per_ip_per_minute", 120)
    )

    limiters: list[tuple[TokenBucket, Callable[[Request], str], str]] = []
    if global_per_minute > 0:
        limiters.append(
            (TokenBucket(global_per_minute, global_per_minute), lambda _r: "*", "global")
        )
    if per_ip_per_minute > 0:

        def _ip_key(r: Request) -> str:
            # FastAPI's client may be None in some test contexts
            host = getattr(getattr(r, "client", None), "host", None) or "unknown"
            return host

        limiters.append((TokenBucket(per_ip_per_minute, per_ip_per_minute), _ip_key, "per_ip"))
    return limiters


def rate_limit_middleware_factory(
    limiters: list[tuple[TokenBucket, Callable[[Request], str], str]],
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    """Return a FastAPI-compatible middleware coroutine implementing the limiters."""

    async def _middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:  # pragma: no cover - rejection path partially covered by tests in future
        for bucket, key_func, scope in limiters:
            key = key_func(request)
            if not bucket.allow(key):
                RATE_LIMIT_REJECTS.labels(scope=scope).inc()
                log.info("rate_limited", scope=scope, key=key, path=request.url.path)
                return JSONResponse({"detail": "rate_limited", "scope": scope}, status_code=429)
        return await call_next(request)

    return _middleware


__all__ = [
    "TokenBucket",
    "build_rate_limiters",
    "rate_limit_middleware_factory",
]
