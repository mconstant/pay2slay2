import os
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request, Response

from src.lib.http import correlation_middleware
from src.lib.observability import get_logger, setup_structlog
from src.lib.region import infer_region_from_request


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

    # Create tables if brand new
    Base.metadata.create_all(bind=engine)

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


def create_app() -> FastAPI:
    """Create and return the FastAPI application instance."""
    setup_structlog()
    log = get_logger(__name__)
    app = FastAPI(title="Pay2Slay API", version="0.1.0")
    # Add correlation/trace middleware early
    app.middleware("http")(correlation_middleware)

    @app.middleware("http")
    async def region_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.region_code = infer_region_from_request(request)
        return await call_next(request)

    try:  # Config load
        from src.lib.config import get_config  # local import

        app.state.config = get_config()
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
    from .user import router as user_router

    app.include_router(auth_router)
    app.include_router(config_router)
    app.include_router(user_router)
    app.include_router(admin_router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:  # pragma: no cover
        return {"status": "ok"}

    @app.get("/livez")
    def livez() -> dict[str, str]:  # pragma: no cover
        # If the process is up, liveness is ok
        return {"status": "alive"}

    @app.get("/readyz")
    def readyz() -> dict[str, str]:  # pragma: no cover
        # Basic readiness: ensure DB session can be created
        try:
            session_factory = getattr(app.state, "session_factory", None)
            if session_factory is None:
                return {"status": "not_ready"}
            session = session_factory()
            try:
                # do a trivial no-op
                session.execute("SELECT 1")
            finally:
                session.close()
            return {"status": "ready"}
        except Exception:
            return {"status": "not_ready"}

    return app
