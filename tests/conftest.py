import pytest
from fastapi.testclient import TestClient


# The app factory is expected at src.api.app:create_app
# Tests will initially fail until the app and endpoints are implemented.
@pytest.fixture(scope="session")
def app():
    from src.api.app import create_app  # type: ignore[attr-defined]

    return create_app()


@pytest.fixture()
def client(app):
    return TestClient(app)
