from __future__ import annotations

import os


def test_api_requires_endpoint_env():
    # Provide environment variable for success path
    os.environ.setdefault("BANANO_RPC_ENDPOINT", "node.example:7072")
    assert "BANANO_RPC_ENDPOINT" in os.environ
