from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import structlog
from opentelemetry import trace  # type: ignore[import-not-found]
from opentelemetry.sdk.resources import Resource  # type: ignore[import-not-found]
from opentelemetry.sdk.trace import TracerProvider  # type: ignore[import-not-found]
from opentelemetry.sdk.trace.export import (  # type: ignore[import-not-found]
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

OTLPSpanExporter = None  # Placeholder; add dependency and import when enabling OTLP export

_TRACER_INITIALIZED = False


def setup_structlog(level: str | int = "INFO") -> None:
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(message)s",
    )
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )
    global _TRACER_INITIALIZED  # noqa: PLW0603
    if not _TRACER_INITIALIZED:
        resource = Resource.create({"service.name": "pay2slay"})
        provider = TracerProvider(resource=resource)
        # Always console exporter in dev
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        # TODO: Add OTLP exporter when dependency is included
        trace.set_tracer_provider(provider)
        _TRACER_INITIALIZED = True


def get_logger(*args: Any, **kwargs: Any) -> Any:
    return structlog.get_logger(*args, **kwargs)


def get_tracer(name: str = "app") -> Any:
    return trace.get_tracer(name)


def instrument_http_call(
    name: str,
    func: Callable[[], Any],
    attrs: dict[str, Any] | None = None,
    record_exception: bool = True,
) -> Any:
    """Wrap a synchronous HTTP call in a span.

    Parameters:
        name: span name (e.g., "yunite.get_member")
        func: thunk performing the HTTP request and returning a value
        attrs: optional span attributes
        record_exception: whether to record exceptions
    Returns:
        Value returned by func
    """
    tracer = get_tracer("http-client")
    span = tracer.start_span(name, attributes=attrs or {})
    start = time.time()
    try:
        result = func()
        span.set_attribute("http.duration_ms", (time.time() - start) * 1000.0)
        return result
    except Exception as exc:  # pragma: no cover - network variability
        if record_exception:
            try:
                span.record_exception(exc)
            except Exception:  # pragma: no cover
                pass
        span.set_attribute("error", True)
        raise
    finally:
        span.end()


__all__ = ["get_logger", "get_tracer", "setup_structlog", "instrument_http_call"]
