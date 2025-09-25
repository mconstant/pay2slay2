from http import HTTPStatus


def test_config_product_endpoint(client):
    resp = client.get("/config/product")
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    for key in ("app_name", "org_name", "default_locale", "feature_flags"):
        assert key in data
    assert isinstance(data["feature_flags"], dict)
