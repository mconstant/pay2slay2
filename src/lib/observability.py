from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from typing import Any, no_type_check

import structlog

try:  # Optional Prometheus dependency (already in deps, but guard defensively)
    from prometheus_client import Counter

    _PROM_AVAILABLE = True
except Exception:  # pragma: no cover
    Counter = None  # type: ignore
    _PROM_AVAILABLE = False

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

OTLPSpanExporter: Any | None = None  # Populated if OTLP exporter dependency available
try:  # Optional OTLP exporter (http/proto) dependency
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore
        OTLPSpanExporter as _OTLPSpanExporter,
    )

    OTLPSpanExporter = _OTLPSpanExporter
except Exception:  # pragma: no cover
    OTLPSpanExporter = None

_TRACER_INITIALIZED = False


def setup_structlog(level: str | int = "INFO") -> None:
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(message)s",
    )

    # Trace context enrichment processor (added early so later processors can use ids)
    def _add_trace_context(_: Any, __: str, event_dict: Any) -> Any:
        """If a current span exists, add trace_id/span_id (hex) when not already present."""
        if not _OTEL_AVAILABLE or _TRACE_MOD is None:
            return event_dict
        try:
            span = _TRACE_MOD.get_current_span()
            if not span:
                return event_dict
            ctx = span.get_span_context()
            trace_id = getattr(ctx, "trace_id", 0)
            span_id = getattr(ctx, "span_id", 0)
            # Only add if ids are non-zero (OTel spec: 0 means invalid)
            if trace_id and "trace_id" not in event_dict:
                try:
                    event_dict["trace_id"] = f"{trace_id:032x}"  # int -> 32 hex chars
                except Exception:  # pragma: no cover
                    pass
            if span_id and "span_id" not in event_dict:
                try:
                    event_dict["span_id"] = f"{span_id:016x}"
                except Exception:  # pragma: no cover
                    pass
        except Exception:  # pragma: no cover - never break logging
            return event_dict
        return event_dict

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            _add_trace_context,
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

            # Decide exporter(s): if OTLP endpoint configured and exporter available, prefer it; always include console if no OTLP
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or os.getenv(
                "PAY2SLAY_OTLP_ENDPOINT"
            )
            exporters: list[Any] = []
            if otlp_endpoint and OTLPSpanExporter is not None:
                try:
                    exporters.append(OTLPSpanExporter(endpoint=otlp_endpoint))
                except Exception:  # pragma: no cover
                    logging.getLogger("observability").warning(
                        "otlp_exporter_init_failed endpoint=%s", otlp_endpoint
                    )
            if not exporters:  # Fallback to console exporter
                exporters.append(ConsoleSpanExporter())
            for exp in exporters:
                provider.add_span_processor(BatchSpanProcessor(exp))
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
    "instrument_http_call",
    "instrument_sqlalchemy",
    "setup_structlog",
    "record_image_build",
    "record_rollback",
    "get_metric_value",
]

# --------------------------------------------------------------------------------------
# Metrics (T022): lightweight dual-path metrics (Prometheus counter + in-process mirror)
# Counters:
#   image_build_total{repository_type="canonical|staging|unknown"}
#   rollback_total{repository_type="canonical|staging|unknown"}
# Exported helpers record_image_build / record_rollback keep tests simple without requiring
# a running Prometheus exporter. get_metric_value(key) used in unit tests (T052) while
# prometheus_client Counter remains the production instrumentation path. (T060 doc update)
# --------------------------------------------------------------------------------------

_METRIC_COUNTS: dict[str, int] = {}

if _PROM_AVAILABLE:
    _IMAGE_BUILD_COUNTER = Counter(
        "image_build_total", "Total number of image builds", ["repository_type"]
    )
    _ROLLBACK_COUNTER = Counter(
        "rollback_total", "Total number of rollbacks performed", ["repository_type"]
    )
else:  # pragma: no cover - fallback
    _IMAGE_BUILD_COUNTER = None  # type: ignore
    _ROLLBACK_COUNTER = None  # type: ignore


def _inc(key: str) -> None:
    _METRIC_COUNTS[key] = _METRIC_COUNTS.get(key, 0) + 1


def record_image_build(repository_type: str) -> None:
    """Increment image build counter for repository_type (T022)."""
    key = f"image_build_total|{repository_type}"
    _inc(key)
    if _PROM_AVAILABLE and _IMAGE_BUILD_COUNTER is not None:  # pragma: no branch
        try:
            _IMAGE_BUILD_COUNTER.labels(repository_type=repository_type).inc()
        except Exception:  # pragma: no cover
            pass


def record_rollback(repository_type: str) -> None:
    """Increment rollback counter for repository_type (T022)."""
    key = f"rollback_total|{repository_type}"
    _inc(key)
    if _PROM_AVAILABLE and _ROLLBACK_COUNTER is not None:  # pragma: no branch
        try:
            _ROLLBACK_COUNTER.labels(repository_type=repository_type).inc()
        except Exception:  # pragma: no cover
            pass


def get_metric_value(key: str) -> int:
    """Return in-process metric value (used by unit tests)."""
    return _METRIC_COUNTS.get(key, 0)
