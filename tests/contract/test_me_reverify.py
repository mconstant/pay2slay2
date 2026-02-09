from http import HTTPStatus


def test_me_reverify_requires_auth(client):
    resp = client.post("/me/reverify")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_me_reverify_success_path(client):
    # Precondition: user session
    client.get("/auth/discord/callback?state=xyz&code=dummy")
    r = client.post("/me/reverify")
    assert r.status_code in (HTTPStatus.ACCEPTED, HTTPStatus.OK)
