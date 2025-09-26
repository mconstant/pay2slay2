from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any, no_type_check

import structlog

_TRACE_MOD: Any | None = None
Resource: Any | None = None
TracerProvider: Any | None = None
BatchSpanProcessor: Any | None = None
ConsoleSpanExporter: Any | None = None
try:  # Optional OpenTelemetry dependency
    from opentelemetry import trace as _trace_mod  # type: ignore
    from opentelemetry.sdk.resources import Resource as _Resource  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider as _TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import (  # type: ignore
        BatchSpanProcessor as _BatchSpanProcessor,
    )
    from opentelemetry.sdk.trace.export import (
        ConsoleSpanExporter as _ConsoleSpanExporter,
    )

    _TRACE_MOD = _trace_mod
    Resource = _Resource
    TracerProvider = _TracerProvider
    BatchSpanProcessor = _BatchSpanProcessor
    ConsoleSpanExporter = _ConsoleSpanExporter
    _OTEL_AVAILABLE = True
except Exception:  # pragma: no cover
    _OTEL_AVAILABLE = False

event: Any | None = None
try:  # Optional SQLAlchemy dependency
    from sqlalchemy import event as _sqla_event

    event = _sqla_event
    _SQLA_AVAILABLE = True
except Exception:  # pragma: no cover
    _SQLA_AVAILABLE = False

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
    if (
        _OTEL_AVAILABLE
        and not _TRACER_INITIALIZED
        and _TRACE_MOD is not None
        and Resource
        and TracerProvider
        and BatchSpanProcessor
        and ConsoleSpanExporter
    ):
        try:
            resource = Resource.create({"service.name": "pay2slay"})
            provider = TracerProvider(resource=resource)
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
            _TRACE_MOD.set_tracer_provider(provider)
            _TRACER_INITIALIZED = True
        except Exception:  # pragma: no cover
            pass


def get_logger(*args: Any, **kwargs: Any) -> Any:
    return structlog.get_logger(*args, **kwargs)


def get_tracer(name: str = "app") -> Any:
    if not _OTEL_AVAILABLE or _TRACE_MOD is None:

        class _NoopTracer:  # pragma: no cover - simple fallback
            def start_span(self, *_a: Any, **_k: Any) -> Any:
                class _Span:
                    def set_attribute(self, *_a: Any, **_k: Any) -> None:
                        return None

                    def end(self) -> None:
                        return None

                return _Span()

            def start_as_current_span(self, *_a: Any, **_k: Any) -> Any:  # context manager support
                from contextlib import contextmanager

                @contextmanager
                def _cm() -> Any:
                    span = self.start_span()
                    try:
                        yield span
                    finally:
                        span.end()

                return _cm()

        return _NoopTracer()
    return _TRACE_MOD.get_tracer(name)


def instrument_sqlalchemy(engine: Any) -> None:  # pragma: no cover - runtime instrumentation
    """Attach simple span hooks for SQLAlchemy core execute events.

    Creates one span per statement with basic attributes; avoids binding large parameter
    payloads to keep overhead low. Idempotent if called multiple times.
    """
    tracer = get_tracer("sqlalchemy")

    if (not _SQLA_AVAILABLE) or (not _OTEL_AVAILABLE) or (_TRACE_MOD is None) or (event is None):
        return
    if getattr(engine, "_otel_instrumented", False):
        return

    if event is None:  # pragma: no cover
        return

    @no_type_check
    @event.listens_for(engine, "before_cursor_execute")  # pragma: no cover
    def _before_cursor_execute(*args: Any) -> None:
        # Signature: (conn, cursor, statement, parameters, context, executemany)
        try:
            conn, _cursor, statement, _parameters, context, executemany = args
        except Exception:  # pragma: no cover - defensive
            return
        span = tracer.start_span(
            "db.statement",
            attributes={
                "db.system": getattr(getattr(conn, "engine", None), "name", "unknown"),
                "db.statement": str(statement).strip().split("\n")[0][:500],
                "db.executemany": bool(executemany),
            },
        )
        try:
            context._otel_span = span
        except Exception:  # pragma: no cover
            span.end()

    @no_type_check
    @event.listens_for(engine, "after_cursor_execute")  # pragma: no cover
    def _after_cursor_execute(*args: Any) -> None:
        # Signature: (conn, cursor, statement, parameters, context, executemany)
        try:
            _conn, _cursor, _statement, _parameters, context, _executemany = args
        except Exception:  # pragma: no cover
            return
        span = getattr(context, "_otel_span", None)
        if span is not None:
            try:
                span.end()
            except Exception:  # pragma: no cover
                pass

    @no_type_check
    @event.listens_for(engine, "handle_error")  # pragma: no cover
    def _handle_error(*args: Any) -> None:
        # Signature (exception_context)
        if not args:
            return
        exception_context = args[0]
        span = getattr(getattr(exception_context, "execution_context", None), "_otel_span", None)
        if span is not None:
            try:
                span.set_attribute("error", True)
                span.record_exception(getattr(exception_context, "original_exception", None))
            except Exception:  # pragma: no cover
                pass
            finally:
                try:
                    span.end()
                except Exception:  # pragma: no cover
                    pass

    try:
        engine._otel_instrumented = True
    except Exception:  # pragma: no cover
        pass


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
        try:
            span.set_attribute("http.duration_ms", (time.time() - start) * 1000.0)
        except Exception:  # pragma: no cover
            pass
        return result
    except Exception as exc:  # pragma: no cover - network variability
        if record_exception:
            try:
                try:
                    span.record_exception(exc)
                except Exception:  # pragma: no cover
                    pass
            except Exception:  # pragma: no cover
                pass
        try:
            span.set_attribute("error", True)
        except Exception:  # pragma: no cover
            pass
        raise
    finally:
        try:
            span.end()
        except Exception:  # pragma: no cover
            pass


__all__ = [
    "get_logger",
    "get_tracer",
    "setup_structlog",
    "instrument_http_call",
    "instrument_sqlalchemy",
]
