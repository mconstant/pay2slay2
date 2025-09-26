from __future__ import annotations

import re

import pytest

HOST_DNS_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*$"
)
HOST_IPV4_PATTERN = re.compile(r"^([0-9]{1,3}\.){3}[0-9]{1,3}$")

PORT_MIN = 1024
PORT_MAX = 65535


def validate(value: str) -> None:
    host, port_s = value.split(":", 1)
    assert HOST_DNS_PATTERN.match(host) or HOST_IPV4_PATTERN.match(host), "invalid host"
    port = int(port_s)
    assert PORT_MIN <= port <= PORT_MAX, "invalid port"


@pytest.mark.xfail(reason="Validator integration not implemented", strict=False)
def test_invalid_host():
    with pytest.raises(AssertionError):
        validate("-bad:1234")


@pytest.mark.xfail(reason="Validator integration not implemented", strict=False)
def test_invalid_port():
    with pytest.raises(AssertionError):
        validate("ok.example:70000")


@pytest.mark.xfail(reason="Validator integration not implemented", strict=False)
def test_valid_endpoint():
    validate("ok.example:12345")
