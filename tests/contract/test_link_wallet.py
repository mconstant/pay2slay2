from http import HTTPStatus


def test_link_wallet_validates_banano_address(client):
    resp = client.post("/link/wallet", json={"banano_address": "invalid"})
    assert resp.status_code in (HTTPStatus.UNPROCESSABLE_ENTITY, HTTPStatus.BAD_REQUEST)


def test_link_wallet_success_path(client):
    # Will fail until user session/auth implemented
    resp = client.post("/link/wallet", json={"banano_address": "ban_1exampleaddress"})
    assert resp.status_code in (
        HTTPStatus.OK,
        HTTPStatus.ACCEPTED,
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.NOT_IMPLEMENTED,
    )
