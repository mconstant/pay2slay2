from http import HTTPStatus


def test_auth_callback_requires_state_and_code(client):
    # Missing params should be rejected
    resp = client.get("/auth/discord/callback", follow_redirects=False)
    assert resp.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY)


def test_auth_callback_success(client):
    # Dry-run flow should succeed with a redirect and session cookie
    resp = client.get("/auth/discord/callback?state=xyz&code=dummy", follow_redirects=False)
    assert resp.status_code == HTTPStatus.FOUND  # 302 redirect
    assert "p2s_session" in resp.cookies


def test_auth_callback_invalid_state(client):
    resp = client.get("/auth/discord/callback?state=badtoken&code=dummy", follow_redirects=False)
    # Should reject invalid state now
    assert resp.status_code == HTTPStatus.BAD_REQUEST
