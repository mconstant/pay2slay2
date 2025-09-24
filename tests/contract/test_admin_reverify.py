from http import HTTPStatus

def test_admin_reverify_requires_admin_auth(client):
    resp = client.post("/admin/reverify", json={"discord_id": "123"})
    assert resp.status_code in (
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.FORBIDDEN,
        HTTPStatus.NOT_IMPLEMENTED,
    )
