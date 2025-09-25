import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# The app factory is expected at src.api.app:create_app
# Tests will initially fail until the app and endpoints are implemented.
@pytest.fixture(scope="session")
def app():
    # Use a fresh temporary sqlite DB per test session to ensure migrations apply cleanly
    tmp_dir = tempfile.mkdtemp(prefix="p2s_test_")
    db_path = os.path.join(tmp_dir, "test.db")
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path}")
    os.environ.setdefault("PAY2SLAY_AUTO_MIGRATE", "1")
    from src.api.app import create_app  # type: ignore[attr-defined]

    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def db_session(app) -> Session:  # type: ignore[override]
    session_factory = app.state.session_factory
    session: Session = session_factory()
    try:
        yield session
    finally:
        session.close()
