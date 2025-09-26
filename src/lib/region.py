from __future__ import annotations

from fastapi import Request
from prometheus_client import Counter

REGION_HEADER = "X-Region"

# Metrics around region detection
REGION_HEADER_PRESENT = Counter(
    "region_header_present_total", "Requests with explicit region header"
)
REGION_INFERRED = Counter("region_inferred_total", "Requests where region inferred from IP")
REGION_UNKNOWN = Counter("region_unknown_total", "Requests without region info")

_PRIVATE_PREFIXES = ("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.")


def _infer_from_ip(ip: str | None) -> str | None:
    """Very rough placeholder for GeoIP mapping.

    For now returns None for private ranges; else returns country-like code stub 'ZZ'.
    Replace with real GeoIP (maxmind or ip2location) later.
    """
    if not ip:
        return None
    if any(ip.startswith(p) for p in _PRIVATE_PREFIXES):
        return None
    # Real implementation would look up IP here
    return "ZZ"


def _normalize(code: str | None) -> str | None:
    if not code:
        return None
    code = code.strip().upper()
    if not code:
        return None
    # Bound to 8 chars (db column size)
    return code[:8]


def infer_region_from_request(request: Request) -> str | None:  # pragma: no cover - simple
    header_val = request.headers.get(REGION_HEADER)
    if header_val:
        REGION_HEADER_PRESENT.inc()
        return _normalize(header_val)
    # Attempt IP-based inference
    ip = request.client.host if request.client else None
    inferred = _infer_from_ip(ip)
    if inferred:
        REGION_INFERRED.inc()
        return _normalize(inferred)
    REGION_UNKNOWN.inc()
    return None


__all__ = [
    "REGION_HEADER",
    "REGION_HEADER_PRESENT",
    "REGION_INFERRED",
    "REGION_UNKNOWN",
    "infer_region_from_request",
]
