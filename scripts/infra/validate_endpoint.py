#!/usr/bin/env python3
"""Validate Banano RPC endpoint host:port string.

Exit status:
 0 valid
 1 invalid format
"""

from __future__ import annotations

import re
import sys

HOST_DNS = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*$")
HOST_IPV4 = re.compile(r"^([0-9]{1,3}\.){3}[0-9]{1,3}$")
PORT_MIN, PORT_MAX = 1024, 65535
EXPECTED_ARGS = 2  # script name + endpoint


def valid(endpoint: str) -> bool:
    if ":" not in endpoint:
        return False
    host, port_s = endpoint.split(":", 1)
    if not host.strip():
        return False
    if not (HOST_DNS.match(host) or HOST_IPV4.match(host)):
        return False
    if not port_s.isdigit():
        return False
    port = int(port_s)
    if not (PORT_MIN <= port <= PORT_MAX):
        return False
    return True


def main() -> int:
    if len(sys.argv) != EXPECTED_ARGS:
        print("usage: validate_endpoint.py <host:port>", file=sys.stderr)
        return 1
    ep = sys.argv[1]
    if not valid(ep):
        print(f"INVALID_ENDPOINT {ep}", file=sys.stderr)
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
