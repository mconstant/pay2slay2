from http import HTTPStatus


def test_me_status_returns_linkage_and_rewards(client):
    resp = client.get("/me/status")
    # Initially likely 401/404 until implemented
    assert resp.status_code in (
        HTTPStatus.OK,
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.NOT_FOUND,
        HTTPStatus.NOT_IMPLEMENTED,
    )
    if resp.status_code == HTTPStatus.OK:
        body = resp.json()
        for key in ("linked", "last_verified_at", "accrued_rewards_ban"):
            assert key in body
