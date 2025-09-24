from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and return the FastAPI application instance.

    Endpoints will be registered in subsequent tasks. For now, this exists to
    allow contract tests to run and fail meaningfully (404/validation) under TDD.
    """
    app = FastAPI(title="Pay2Slay API", version="0.1.0")

    from .auth import router as auth_router
    from .user import router as user_router
    from .admin import router as admin_router

    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(admin_router)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:  # pragma: no cover
        return {"status": "ok"}

    return app
