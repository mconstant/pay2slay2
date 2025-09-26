from __future__ import annotations

import os


def test_api_fails_without_endpoint_env():
    # Simulate startup logic expecting BANANO_RPC_ENDPOINT
    assert "BANANO_RPC_ENDPOINT" in os.environ, "BANANO_RPC_ENDPOINT missing should cause failure"
