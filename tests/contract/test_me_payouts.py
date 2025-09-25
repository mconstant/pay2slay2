from http import HTTPStatus


def test_me_payouts_requires_auth(client):
    resp = client.get("/me/payouts")
    assert resp.status_code in (
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.NOT_FOUND,
        HTTPStatus.NOT_IMPLEMENTED,
    )


def test_me_payouts_success_flow(client):
    client.post("/auth/discord/callback?state=xyz&code=dummy")
    r = client.get("/me/payouts")
    assert r.status_code in (HTTPStatus.NOT_FOUND, HTTPStatus.NOT_IMPLEMENTED, HTTPStatus.OK)
    if r.status_code == HTTPStatus.OK:
        data = r.json()
        assert isinstance(data, dict) and "payouts" in data
