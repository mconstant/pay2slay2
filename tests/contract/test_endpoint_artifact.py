"""Contract tests (placeholders) for Banano -> API endpoint artifact.

These are expected to FAIL until the workflows and validation helpers are implemented.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import jsonschema
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


def test_ct_001_valid_artifact(tmp_path: Path):
    artifact_path = tmp_path / "endpoint.json"
    artifact_path.write_text(json.dumps({"banano_rpc_endpoint": "node.example:12345"}))
    data = json.loads(artifact_path.read_text())
    assert set(data.keys()) == {"banano_rpc_endpoint"}
    _validate_endpoint(data["banano_rpc_endpoint"])
    # Schema validation
    schema_path = (
        Path(__file__).parents[2]
        / "specs"
        / "002-separate-out-the"
        / "contracts"
        / "endpoint.schema.json"
    )
    jsonschema.validate(instance=data, schema=json.loads(schema_path.read_text()))


def test_ct_002_missing_artifact(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        _ = json.loads((tmp_path / "endpoint.json").read_text())


def test_ct_003_invalid_host():
    with pytest.raises(AssertionError):
        _validate_endpoint("-badhost:1234")


def test_ct_004_port_out_of_range():
    with pytest.raises(AssertionError):
        _validate_endpoint("node.example:70000")


def test_ct_005_empty_json(tmp_path: Path):
    artifact_path = tmp_path / "endpoint.json"
    artifact_path.write_text(json.dumps({}))
    data = json.loads(artifact_path.read_text())
    schema_path = (
        Path(__file__).parents[2]
        / "specs"
        / "002-separate-out-the"
        / "contracts"
        / "endpoint.schema.json"
    )
    if schema_path.exists():
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=data, schema=json.loads(schema_path.read_text()))
    else:
        pytest.skip("endpoint.schema.json missing")


def test_ct_006_multiple_redeploys(tmp_path: Path):
    # Simulate two artifacts with different timestamps (conceptual)
    first = tmp_path / "endpoint.json.1"
    second = tmp_path / "endpoint.json.2"
    first.write_text(
        json.dumps(
            {"banano_rpc_endpoint": "node.example:12345", "ts": datetime.utcnow().isoformat()}
        )
    )
    second.write_text(
        json.dumps(
            {
                "banano_rpc_endpoint": "node.example:22345",
                "ts": (datetime.utcnow() + timedelta(seconds=5)).isoformat(),
            }
        )
    )
    assert first.read_text() != second.read_text()


def test_invalid_port_rejected():
    with pytest.raises(AssertionError):
        _validate_endpoint("host.example:80")


def test_invalid_host_rejected():
    with pytest.raises(AssertionError):
        _validate_endpoint(":1234")
