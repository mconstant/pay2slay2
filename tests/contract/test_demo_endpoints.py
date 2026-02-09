"""Contract tests for demo-only endpoints (dry-run mode)."""

from http import HTTPStatus


def test_demo_login_returns_user(client):
    resp = client.post("/auth/demo-login")
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["discord_user_id"] == "demo_user_001"
    assert data["discord_username"] == "DemoPlayer"
    assert data["epic_account_id"] == "epic_demo_001"
    assert "p2s_session" in resp.cookies


def test_demo_login_is_idempotent(client):
    r1 = client.post("/auth/demo-login")
    r2 = client.post("/auth/demo-login")
    assert r1.json()["discord_user_id"] == r2.json()["discord_user_id"]


def test_demo_seed_creates_data(client):
    client.post("/auth/demo-login")
    resp = client.post("/demo/seed")
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert "summary" in data
    assert data["accruals"] >= 0
    assert data["payouts"] >= 0


def test_demo_seed_idempotent(client):
    client.post("/auth/demo-login")
    r1 = client.post("/demo/seed")
    r2 = client.post("/demo/seed")
    assert r1.status_code == HTTPStatus.OK
    assert r2.status_code == HTTPStatus.OK


def test_demo_run_scheduler(client):
    # Login + seed first so there are users to process
    r = client.post("/auth/demo-login")
    cookies = r.cookies
    client.post("/demo/seed", cookies=cookies)

    resp = client.post("/demo/run-scheduler", cookies=cookies)
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert "accrued" in data
    assert "settled" in data
    assert data["accrued"] >= 0
    assert data["settled"] >= 0


def test_demo_login_then_status(client):
    """Full flow: demo login -> status should show verified user."""
    r = client.post("/auth/demo-login")
    cookies = r.cookies
    resp = client.get("/me/status", cookies=cookies)
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert data["last_verified_status"] == "ok"


def test_demo_login_then_seed_then_accruals(client):
    """Full flow: login -> seed -> accruals should have data."""
    r = client.post("/auth/demo-login")
    cookies = r.cookies
    client.post("/demo/seed", cookies=cookies)
    resp = client.get("/me/accruals", cookies=cookies)
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["count"] > 0


def test_demo_admin_flow(client):
    """Demo login -> seed (creates admin) -> admin login -> stats."""
    client.post("/auth/demo-login")
    client.post("/demo/seed")
    r = client.post("/admin/login", json={"email": "admin@example.org"})
    assert r.status_code == HTTPStatus.OK
    cookies = r.cookies
    resp = client.get("/admin/stats", cookies=cookies)
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["users_total"] > 0


def test_static_index_served(client):
    resp = client.get("/")
    assert resp.status_code == HTTPStatus.OK
    assert "<!DOCTYPE html>" in resp.text


def test_static_css_served(client):
    resp = client.get("/static/style.css")
    assert resp.status_code == HTTPStatus.OK
    assert "Pay2Slay" in resp.text


def test_static_js_served(client):
    resp = client.get("/static/app.js")
    assert resp.status_code == HTTPStatus.OK
    assert "demoLogin" in resp.text
