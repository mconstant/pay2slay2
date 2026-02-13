import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from src.lib.http import correlation_middleware
from src.lib.observability import get_logger, setup_structlog
from src.lib.ratelimit import build_rate_limiters, rate_limit_middleware_factory
from src.lib.region import infer_region_from_request

_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


def _ensure_schema_columns(engine: Any, log: Any) -> None:
    """Idempotently add columns that migrations would add.

    Handles the gap where create_all() created tables from an older model
    but Alembic migrations couldn't run (e.g. init migration conflicts).
    """
    from sqlalchemy import text

    additions = [
        ("payouts", "idempotency_key", "VARCHAR(128)"),
        ("payouts", "attempt_count", "INTEGER DEFAULT 1"),
        ("payouts", "first_attempt_at", "DATETIME"),
        ("payouts", "last_attempt_at", "DATETIME"),
        ("payouts", "error_detail", "VARCHAR(500)"),
        ("users", "last_settled_kill_count", "INTEGER DEFAULT 0"),
        ("users", "last_settlement_at", "DATETIME"),
        ("users", "region_code", "VARCHAR(8)"),
        ("users", "abuse_flags", "VARCHAR(500)"),
    ]
    with engine.connect() as conn:
        for table, col, col_type in additions:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                conn.commit()
                log.info("schema_added_column", table=table, column=col)
            except Exception:
                pass  # Column already exists


def _init_db(app: FastAPI, log: Any) -> None:
    from src.lib.db import make_engine, make_session_factory  # local import
    from src.models.base import Base

    db_url = (
        getattr(app.state.config, "database_url", None) if hasattr(app.state, "config") else None
    )
    # Import models early so metadata has full schema before create_all/migrations
    from src.models import models  # noqa: F401  # pylint: disable=unused-import

    engine = make_engine(db_url)
    session_factory = make_session_factory(engine)
    app.state.engine = engine
    app.state.session_factory = session_factory

    # Optional SQLAlchemy tracing instrumentation
    try:  # pragma: no cover - instrumentation best-effort
        from src.lib.observability import instrument_sqlalchemy  # local import

        instrument_sqlalchemy(engine)
    except Exception as exc:  # pragma: no cover
        log.warning("db_tracing_instrument_failed", error=str(exc))

    # Create tables if brand new
    Base.metadata.create_all(bind=engine)

    # Ensure columns that migrations would add exist (handles create_all/migration gaps)
    _ensure_schema_columns(engine, log)

    # Apply migrations for column additions / constraints
    if os.getenv("PAY2SLAY_AUTO_MIGRATE") == "1":  # pragma: no cover
        try:
            from alembic import command as alembic_command
            from alembic.config import Config as AlembicConfig

            cfg = AlembicConfig("alembic.ini")
            if db_url:
                cfg.set_main_option("sqlalchemy.url", db_url)
            log.info("alembic_upgrade_start", url=db_url or "default")
            alembic_command.upgrade(cfg, "head")
            log.info("alembic_upgrade_complete")
        except Exception as mig_exc:  # pragma: no cover
            log.warning("alembic_upgrade_failed", error=str(mig_exc))


def _register_metrics(app: FastAPI) -> None:
    """Attach /metrics endpoint (kept separate to reduce create_app complexity)."""

    @app.get("/metrics")
    def metrics() -> PlainTextResponse:  # pragma: no cover - scraped externally
        try:
            from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

            data = generate_latest()
            return PlainTextResponse(data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
        except Exception as exc:  # pragma: no cover
            return PlainTextResponse(f"error generating metrics: {exc}", status_code=500)


def _register_health(app: FastAPI) -> None:
    """Register health, live, and readiness probes (kept small for PLR0915)."""

    @app.get("/healthz")
    def healthz() -> dict[str, str]:  # pragma: no cover
        return {"status": "ok", "version": os.environ.get("IMAGE_TAG", "dev")}

    @app.get("/livez")
    def livez() -> dict[str, str]:  # pragma: no cover
        return {"status": "alive"}

    @app.get("/readyz")
    def readyz() -> dict[str, str]:  # pragma: no cover
        try:
            session_factory = getattr(app.state, "session_factory", None)
            if session_factory is None:
                return {"status": "not_ready"}
            session = session_factory()
            try:
                session.execute("SELECT 1")
            finally:
                session.close()
            return {"status": "ready"}
        except Exception:
            return {"status": "not_ready"}


def create_app() -> FastAPI:  # noqa: PLR0915 - acceptable aggregated startup logic
    """Create and return the FastAPI application instance."""
    # Load .env before anything reads os.getenv
    from dotenv import load_dotenv

    load_dotenv()

    setup_structlog()
    log = get_logger(__name__)
    app = FastAPI(title="Pay2Slay API", version="0.1.0")
    # Add correlation/trace middleware early
    app.middleware("http")(correlation_middleware)

    # Rate limiting middleware (global + per-IP) before other work
    try:
        cfg_for_limits = getattr(app.state, "config", None)  # may not be loaded yet
        limiters = build_rate_limiters(cfg_for_limits) if cfg_for_limits else []
        if limiters:
            app.middleware("http")(rate_limit_middleware_factory(limiters))
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("ratelimit_init_failed", error=str(exc))

    @app.middleware("http")
    async def region_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.region_code = infer_region_from_request(request)
        return await call_next(request)

    try:  # Config load
        from src.lib.config import get_config  # local import

        app.state.config = get_config()
        try:  # safe masked config log (no secrets)
            log.info("config_loaded", config=app.state.config.safe_dict())
        except Exception:  # pragma: no cover
            pass
        # T064: Production secrets & config audit (fail fast if defaults in non-dry-run mode)
        try:
            integ = app.state.config.integrations
            session_secret = os.getenv("SESSION_SECRET", "dev-secret")
            if not integ.dry_run:
                if session_secret == "dev-secret":
                    raise RuntimeError(
                        "SESSION_SECRET must be overridden in production (dry_run=false)"
                    )
                if not integ.node_rpc or "localhost" in integ.node_rpc:
                    raise RuntimeError(
                        "Banano node_rpc must point to production endpoint when dry_run=false"
                    )
            # Emit dry_run mode metric & log for visibility (T065)
            try:
                from prometheus_client import Gauge  # local import inside block

                _dry_run_gauge = Gauge(
                    "app_dry_run_mode", "1 if application running in dry_run mode"
                )
                _dry_run_gauge.set(1.0 if integ.dry_run else 0.0)
            except Exception:
                pass
            log.info("runtime_mode", dry_run=integ.dry_run)
        except Exception as guard_exc:
            # Store failure reason and raise to prevent partial unsafe startup
            log.error("startup_guard_failed", error=str(guard_exc))
            raise
    except Exception as exc:  # pragma: no cover
        app.state.config_error = str(exc)
        log.warning("config_load_failed", error=str(exc))

    try:  # DB init
        _init_db(app, log)
    except Exception as exc:  # pragma: no cover
        app.state.db_init_error = str(exc)
        log.warning("db_init_failed", error=str(exc))

    from .admin import router as admin_router
    from .auth import router as auth_router
    from .config import router as config_router
    from .demo import router as demo_router
    from .donations import router as donations_router
    from .leaderboard import router as leaderboard_router
    from .user import router as user_router

    app.include_router(auth_router)
    app.include_router(config_router)
    app.include_router(user_router)
    app.include_router(admin_router)
    app.include_router(demo_router)
    app.include_router(leaderboard_router)
    app.include_router(donations_router)

    _register_health(app)
    _register_metrics(app)

    # Serve frontend static files and SPA fallback
    if _STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

        @app.get("/")
        def index() -> FileResponse:  # pragma: no cover
            return FileResponse(
                str(_STATIC_DIR / "index.html"),
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> Response:
        svg = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎮</text></svg>"
        return Response(content=svg, media_type="image/svg+xml")

    return app
