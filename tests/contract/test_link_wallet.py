from http import HTTPStatus


def test_link_wallet_validates_banano_address(client):
    resp = client.post("/link/wallet", json={"banano_address": "invalid"})
    assert resp.status_code in (HTTPStatus.UNPROCESSABLE_ENTITY, HTTPStatus.BAD_REQUEST)


def test_link_wallet_success_path(client):
    # Ensure a user exists via auth dry-run
    client.post("/auth/discord/callback?state=xyz&code=dummy")
    resp = client.post(
        "/link/wallet",
        json={"banano_address": "ban_1exampleaddresslongenoughfortestpurpose"},
    )
    assert resp.status_code in (HTTPStatus.OK, HTTPStatus.ACCEPTED)
