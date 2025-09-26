from http import HTTPStatus


def test_me_status_returns_linkage_and_rewards(client):
    client.post("/auth/discord/callback?state=xyz&code=dummy")
    client.post("/link/wallet", json={"banano_address": "ban_1exampleaddress"})
    resp = client.get("/me/status")
    assert resp.status_code == HTTPStatus.OK
    body = resp.json()
    for key in ("linked", "last_verified_at", "accrued_rewards_ban"):
        assert key in body
