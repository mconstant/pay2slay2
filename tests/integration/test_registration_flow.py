from http import HTTPStatus


def test_full_registration_flow(client):
    """End-to-end registration flow: OAuth callback -> wallet link -> status check.

    Covers T011 integration scenario ensuring:
    - OAuth dry-run callback succeeds and sets session cookie
    - Wallet can be linked after auth
    - /me/status reflects linkage and verification metadata
    """
    # 1. Simulate Discord OAuth callback in dry_run (state 'xyz' allowed for tests)
    # Callback now returns a 302 redirect with session cookie set
    auth_resp = client.get("/auth/discord/callback?state=xyz&code=dummy", follow_redirects=False)
    assert auth_resp.status_code == HTTPStatus.FOUND
    assert "p2s_session" in auth_resp.cookies

    # 2. Link a wallet using same client (session cookie should be preserved)
    wallet_address = "ban_1registrationflowexampleaddress"
    link_resp = client.post("/link/wallet", json={"banano_address": wallet_address})
    assert link_resp.status_code == HTTPStatus.OK
    assert link_resp.json().get("linked") is True

    # 3. Fetch status and validate linkage & verification record metadata
    status_resp = client.get("/me/status")
    assert status_resp.status_code == HTTPStatus.OK
    status = status_resp.json()

    assert status.get("linked") is True, "Expected linked wallet in status"
    # last_verified_* fields populated from auth callback VerificationRecord
    assert status.get("last_verified_at"), "Expected last_verified_at to be set"
    assert status.get("last_verified_status") == "ok"
    assert status.get("last_verified_source") == "auth_callback"
    # No accruals should have happened yet in this isolated flow
    assert float(status.get("accrued_rewards_ban", 0)) == 0.0

    # 4. Idempotency check: second status call consistent
    status_resp2 = client.get("/me/status")
    assert status_resp2.status_code == HTTPStatus.OK
    status2 = status_resp2.json()
    assert status2 == status
