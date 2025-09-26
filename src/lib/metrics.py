from __future__ import annotations

import os

from prometheus_client import Counter, Histogram

# Environment toggle for exemplars (trace correlation in metrics)
_ENABLE_EXEMPLARS = os.getenv("PAY2SLAY_METRICS_EXEMPLARS") == "1"

# NOTE: Be cautious with label cardinality; using raw path can explode series count.
# For now we keep it simple; future improvement: normalize dynamic segments.
REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency (seconds)",
    ["method", "path"],
)


def observe_http(
    method: str, path: str, status: str | int, duration_seconds: float, trace_id: str | None = None
) -> None:
    """Record HTTP request metrics with optional exemplar for trace correlation."""
    try:
        REQUEST_COUNTER.labels(method=method, path=path, status=str(status)).inc()
    except Exception:  # pragma: no cover - metrics should never break
        return
    try:
        if _ENABLE_EXEMPLARS and trace_id:
            # prometheus_client allows exemplar parameter on observe
            REQUEST_LATENCY.labels(method=method, path=path).observe(
                duration_seconds, exemplar={"trace_id": trace_id}
            )
        else:
            REQUEST_LATENCY.labels(method=method, path=path).observe(duration_seconds)
    except Exception:  # pragma: no cover
        pass


__all__ = ["REQUEST_COUNTER", "REQUEST_LATENCY", "observe_http"]
