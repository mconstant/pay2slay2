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
    # Provide deterministic, test-friendly low rate limits so exhaustion tests can be added later
    os.environ.setdefault("RATE_LIMIT_GLOBAL_PER_MINUTE", "120")
    os.environ.setdefault("RATE_LIMIT_PER_IP_PER_MINUTE", "60")
    from src.api.app import create_app  # type: ignore[attr-defined]

    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def db_session(app) -> Session:  # type: ignore[override]
    session_factory = app.state.session_factory
    session: Session = session_factory()
    # Test safeguard: if migration didn't add payout retry columns (rare timing issue), patch them.
    try:
        cols = [r[1] for r in session.execute("PRAGMA table_info(payouts)").fetchall()]
        if "attempt_count" not in cols:
            session.execute("ALTER TABLE payouts ADD COLUMN attempt_count INTEGER DEFAULT 1")
            session.execute("ALTER TABLE payouts ADD COLUMN first_attempt_at DATETIME")
            session.execute("ALTER TABLE payouts ADD COLUMN last_attempt_at DATETIME")
            session.commit()
    except Exception:  # pragma: no cover - best effort
        session.rollback()
    try:
        yield session
    finally:
        session.close()
