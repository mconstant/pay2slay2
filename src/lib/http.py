from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from .observability import get_logger, get_tracer

log = get_logger("http")
tracer = get_tracer("http")


async def correlation_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:  # pragma: no cover
    start = time.time()
    corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    trace_id = None
    span = tracer.start_span("http_request", attributes={"http.target": request.url.path})
    try:
        trace_id = getattr(
            getattr(span.get_span_context(), "trace_id", None), "to_bytes", lambda: None
        )()
    except Exception:
        trace_id = None
    log.bind(correlation_id=corr_id, path=request.url.path, method=request.method)
    response: Response
    try:
        response = await call_next(request)
        return response
    finally:
        duration = time.time() - start
        log.info(
            "http_request",
            correlation_id=corr_id,
            path=request.url.path,
            method=request.method,
            status=getattr(locals().get("response", None), "status_code", "n/a"),
            duration_ms=round(duration * 1000, 2),
            trace_id=trace_id,
        )
        span.end()


__all__ = ["correlation_middleware"]
