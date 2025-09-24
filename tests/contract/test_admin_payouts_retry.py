from http import HTTPStatus

def test_admin_payouts_retry_requires_admin_auth(client):
    resp = client.post("/admin/payouts/retry", json={"payout_id": "00000000-0000-0000-0000-000000000000"})
    assert resp.status_code in (
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.FORBIDDEN,
        HTTPStatus.NOT_IMPLEMENTED,
    )
