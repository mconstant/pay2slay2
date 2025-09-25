from http import HTTPStatus


def test_auth_callback_requires_state_and_code(client):
    # Missing params should be rejected
    resp = client.post("/auth/discord/callback")
    assert resp.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY)


def test_auth_callback_success(client):
    # Dry-run flow should succeed and return identity payload
    resp = client.post("/auth/discord/callback?state=xyz&code=dummy")
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert set(["discord_user_id", "discord_username", "epic_account_id"]).issubset(data.keys())
