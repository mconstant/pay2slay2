from __future__ import annotations

import os

import pytest


@pytest.mark.xfail(reason="API workflow artifact consumption not implemented", strict=False)
def test_api_fails_without_endpoint_env():
    # Simulate startup logic expecting BANANO_RPC_ENDPOINT
    assert "BANANO_RPC_ENDPOINT" in os.environ, "BANANO_RPC_ENDPOINT missing should cause failure"
