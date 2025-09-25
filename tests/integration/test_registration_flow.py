from http import HTTPStatus


def test_registration_flow_end_to_end(client):
    # 1. Auth callback (dry-run)
    auth_resp = client.post("/auth/discord/callback?state=xyz&code=dummy")
    assert auth_resp.status_code == HTTPStatus.OK
    # 2. Link wallet
    wallet_resp = client.post("/link/wallet", json={"banano_address": "ban_1integrationwallet"})
    assert wallet_resp.status_code in (HTTPStatus.OK, HTTPStatus.ACCEPTED)
    # 3. Fetch status
    status_resp = client.get("/me/status")
    assert status_resp.status_code == HTTPStatus.OK
    body = status_resp.json()
    assert body["linked"] is True
    assert "accrued_rewards_ban" in body
    # Baseline: no accruals yet, so rewards may be 0.0
    assert body["accrued_rewards_ban"] in (0, 0.0)
