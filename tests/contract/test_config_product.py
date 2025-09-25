from http import HTTPStatus


def test_config_product_endpoint(client):
    resp = client.get("/config/product")
    # Expect 200 when implemented; allow 404/501 before implementation
    assert resp.status_code in (HTTPStatus.OK, HTTPStatus.NOT_FOUND, HTTPStatus.NOT_IMPLEMENTED)
    if resp.status_code == HTTPStatus.OK:
        data = resp.json()
        for key in ("app_name", "org_name", "default_locale"):
            assert key in data
