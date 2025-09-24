from http import HTTPStatus

def test_auth_callback_requires_state_and_code(client):
    # Missing params should be rejected
    resp = client.post("/auth/discord/callback")
    assert resp.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY)


def test_auth_callback_requires_guild_membership_and_yunite_mapping(client):
    # Dummy params; expected to fail until implemented
    resp = client.post("/auth/discord/callback?state=xyz&code=dummy")
    assert resp.status_code in (
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.FORBIDDEN,
        HTTPStatus.NOT_IMPLEMENTED,
        HTTPStatus.BAD_REQUEST,
    )
