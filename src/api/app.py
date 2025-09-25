from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and return the FastAPI application instance.

    Endpoints will be registered in subsequent tasks. For now, this exists to
    allow contract tests to run and fail meaningfully (404/validation) under TDD.
    """
    app = FastAPI(title="Pay2Slay API", version="0.1.0")

    # Load configuration and attach to app.state
    try:
        from src.lib.config import get_config  # local import to avoid cycles

        app.state.config = get_config()
    except Exception as exc:  # pragma: no cover - do not crash app creation in tests
        # In early TDD, configs may be incomplete; keep app up but mark config load error
        app.state.config_error = str(exc)

    # Initialize DB engine and session factory
    try:
        from src.lib.db import make_engine, make_session_factory
        from src.models.base import Base

        db_url = getattr(app.state.config, "database_url", None) if hasattr(app.state, "config") else None
        engine = make_engine(db_url)
        session_factory = make_session_factory(engine)
        app.state.engine = engine
        app.state.session_factory = session_factory

        # For early development/tests without Alembic, ensure tables exist
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # pragma: no cover
        app.state.db_init_error = str(exc)

    from .admin import router as admin_router
    from .auth import router as auth_router
    from .user import router as user_router

    app.include_router(auth_router)
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
