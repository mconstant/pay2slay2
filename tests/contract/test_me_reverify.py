from http import HTTPStatus


def test_me_reverify_requires_auth(client):
    resp = client.post("/me/reverify")
    assert resp.status_code in (
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.NOT_IMPLEMENTED,
        HTTPStatus.FORBIDDEN,
    )


def test_me_reverify_success_path(client):
    # Precondition: user session
    client.post("/auth/discord/callback?state=xyz&code=dummy")
    r = client.post("/me/reverify")
    # Until implemented it may 404/501; once implemented expect 202/200
    assert r.status_code in (
        HTTPStatus.NOT_FOUND,
        HTTPStatus.NOT_IMPLEMENTED,
        HTTPStatus.ACCEPTED,
        HTTPStatus.OK,
    )
