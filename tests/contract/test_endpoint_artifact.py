"""Contract tests (placeholders) for Banano -> API endpoint artifact.

These are expected to FAIL until the workflows and validation helpers are implemented.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ARTIFACT_SCHEMA_PATTERN = re.compile(r"^[^:]+:[0-9]+$")
HOST_DNS_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*$"
)
HOST_IPV4_PATTERN = re.compile(r"^([0-9]{1,3}\.){3}[0-9]{1,3}$")

PORT_MIN = 1024
PORT_MAX = 65535


def _validate_endpoint(value: str) -> None:
    assert ":" in value, "endpoint must contain host:port"
    host, port_s = value.split(":", 1)
    assert host, "host must be non-empty"
    assert HOST_DNS_PATTERN.match(host) or HOST_IPV4_PATTERN.match(host), "invalid host format"
    assert port_s.isdigit(), "port must be numeric"
    port = int(port_s)
    assert PORT_MIN <= port <= PORT_MAX, "port out of allowed range"


@pytest.mark.xfail(reason="Workflow artifact not yet implemented", strict=False)
def test_endpoint_artifact_schema_round_trip(tmp_path: Path):
    # Placeholder: simulate reading endpoint.json produced by workflow
    artifact_path = tmp_path / "endpoint.json"
    artifact_path.write_text(json.dumps({"banano_rpc_endpoint": "example.invalid:99999"}))

    data = json.loads(artifact_path.read_text())
    assert set(data.keys()) == {"banano_rpc_endpoint"}, "unexpected keys in artifact"
    endpoint = data["banano_rpc_endpoint"]
    assert ARTIFACT_SCHEMA_PATTERN.match(endpoint), "basic host:port pattern failed"
    _validate_endpoint(endpoint)


@pytest.mark.xfail(reason="Negative validation not yet wired", strict=False)
def test_invalid_port_rejected():
    with pytest.raises(AssertionError):
        _validate_endpoint("host.example:80")


@pytest.mark.xfail(reason="Negative validation not yet wired", strict=False)
def test_invalid_host_rejected():
    with pytest.raises(AssertionError):
        _validate_endpoint(":1234")
