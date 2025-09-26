from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from .metrics import observe_http
from .observability import get_logger, get_tracer

log = get_logger("http")
tracer = get_tracer("http")


async def correlation_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:  # pragma: no cover
    start = time.time()
    corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    trace_id: str | None = None
    span = tracer.start_span("http_request", attributes={"http.target": request.url.path})
    try:  # Extract hex trace id if available
        ctx = span.get_span_context()
        raw_tid = getattr(ctx, "trace_id", 0)
        if raw_tid:
            trace_id = f"{raw_tid:032x}"
    except Exception:  # pragma: no cover
        trace_id = None
    log.bind(correlation_id=corr_id, path=request.url.path, method=request.method)
    response: Response
    try:
        response = await call_next(request)
        return response
    finally:
        duration = time.time() - start
        status = getattr(locals().get("response", None), "status_code", "n/a")
        log.info(
            "http_request",
            correlation_id=corr_id,
            path=request.url.path,
            method=request.method,
            status=status,
            duration_ms=round(duration * 1000, 2),
            trace_id=trace_id,
        )
        try:  # metrics
            observe_http(request.method, request.url.path, status, duration, trace_id)
        except Exception:  # pragma: no cover
            pass
        span.end()


__all__ = ["correlation_middleware"]
