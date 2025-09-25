from __future__ import annotations

from fastapi import Request

REGION_HEADER = "X-Region"


def infer_region_from_request(request: Request) -> str | None:  # pragma: no cover - trivial
    # Priority: explicit header, else None (could map IP via GeoIP later)
    return request.headers.get(REGION_HEADER)


__all__ = ["infer_region_from_request", "REGION_HEADER"]
