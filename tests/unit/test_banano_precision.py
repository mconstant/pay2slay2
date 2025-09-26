from __future__ import annotations

from decimal import Decimal

from src.services.banano_client import BananoClient


def test_banano_raw_truncation():
    client = BananoClient(node_url="http://dummy", dry_run=True)
    # Amount with more than 8 decimals should truncate toward zero in raw conversion
    amt = Decimal("0.123456789123")
    raw = client.ban_to_raw(amt)
    # Convert back to BAN (float) and ensure it does not exceed original
    back = client.raw_to_ban(raw)
    assert back <= float(amt)
    # Difference should be less than one raw unit equivalent (epsilon at scale 1e-29)
    epsilon = 1 / (10**29)
    assert float(amt) - back < epsilon * 2  # small cushion
