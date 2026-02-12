from __future__ import annotations

import hashlib
from decimal import ROUND_DOWN, Decimal
from typing import Any

import httpx

_DRYRUN_BALANCE_BAN = 100.0  # Dry-run dummy balance (BAN)

# Banano address encoding alphabet (same as Nano)
_B32_ALPHABET = "13456789abcdefghijkmnopqrstuwxyz"

# Banano seed is 64 hex characters (32 bytes)
_SEED_HEX_LEN = 64


def _bytes_to_b32(data: bytes) -> str:
    """Convert bytes to Nano/Banano base32 encoding."""
    # Pad to 5-bit boundaries
    bits = bin(int.from_bytes(data, "big"))[2:].zfill(len(data) * 8)
    # Pad bits to multiple of 5
    while len(bits) % 5:
        bits = "0" + bits
    result = ""
    for i in range(0, len(bits), 5):
        chunk = int(bits[i : i + 5], 2)
        result += _B32_ALPHABET[chunk]
    return result


def _blake2b_checksum(pubkey: bytes) -> bytes:
    """Compute 5-byte Blake2b checksum for Banano address."""
    h = hashlib.blake2b(pubkey, digest_size=5)
    return h.digest()[::-1]  # Reversed


def seed_to_address(seed_hex: str, index: int = 0) -> str | None:
    """Derive a Banano address from a 64-char hex seed.

    Uses Blake2b to derive private key, then Ed25519-Blake2b to get public key.
    Returns ban_... address or None if derivation fails.
    """
    try:
        # Validate seed format
        if len(seed_hex) != _SEED_HEX_LEN:
            return None
        seed_bytes = bytes.fromhex(seed_hex)

        # Derive private key: blake2b(seed + index as 4-byte big-endian)
        h = hashlib.blake2b(seed_bytes + index.to_bytes(4, "big"), digest_size=32)
        private_key = h.digest()

        # Get public key via Ed25519-Blake2b (Nano/Banano use Blake2b instead of SHA-512)
        import ed25519_blake2b

        signing_key = ed25519_blake2b.SigningKey(private_key)
        public_key = signing_key.get_verifying_key().to_bytes()

        # Encode public key to address
        # Banano address: ban_ + 52 chars (4-bit padding + 256-bit pubkey) + 8 chars checksum
        pubkey_with_padding = b"\x00\x00\x00" + public_key  # 3 bytes padding for 259 bits
        encoded = _bytes_to_b32(pubkey_with_padding)
        # Take last 52 chars (skip padding encoding artifacts)
        encoded = encoded[-52:]

        # Checksum
        checksum = _blake2b_checksum(public_key)
        checksum_encoded = _bytes_to_b32(checksum)[-8:]

        return f"ban_{encoded}{checksum_encoded}"
    except Exception:
        return None


class BananoClient:
    def __init__(self, node_url: str, dry_run: bool = True, seed: str | None = None) -> None:
        self.node_url = node_url
        self.dry_run = dry_run
        self._seed = seed
        self.http = None if dry_run else httpx.Client(timeout=10)
        # Scale: 10^29 raw = 1 BAN
        self._raw_per_ban = 10**29

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        assert not self.dry_run and self.http is not None
        resp = self.http.post(self.node_url, json=payload)
        resp.raise_for_status()
        return resp.json() or {}

    def ban_to_raw(self, amount_ban: float | Decimal) -> str:
        """Convert BAN (Decimal or float) to raw integer units (as string).

        Accepts either float (legacy callers) or Decimal (preferred) and truncates
        toward zero at 29 decimal places (integer raw units). We deliberately avoid
        rounding up to prevent over-paying when converting fractional values.
        """
        if not isinstance(amount_ban, Decimal):  # normalize legacy float callers
            amount_ban = Decimal(str(amount_ban))
        # Ensure non-negative; negative payouts not expected
        if amount_ban < 0:
            amount_ban = Decimal("0")
        # Scale and truncate (quantize then int)
        scaled = (amount_ban * Decimal(self._raw_per_ban)).to_integral_value(rounding=ROUND_DOWN)
        return str(int(scaled))

    def raw_to_ban(self, amount_raw: str | int) -> float:
        try:
            raw = int(amount_raw)
        except Exception:
            return 0.0
        return raw / self._raw_per_ban

    def account_balance(self, account: str) -> tuple[float, float]:
        """Return (balance_ban, pending_ban). Dry-run returns large dummy values."""
        if self.dry_run:
            return (_DRYRUN_BALANCE_BAN, 0.0)
        data = self._post({"action": "account_balance", "account": account})
        bal = self.raw_to_ban(data.get("balance", "0"))
        pending = self.raw_to_ban(data.get("pending", "0"))
        return (bal, pending)

    def send(
        self,
        source_wallet: str,
        to_address: str,
        amount_raw: str,
        amount_ban: Decimal | None = None,
    ) -> str | None:
        if self.dry_run:
            return "dryrun-tx"
        if self._seed:
            from bananopie import RPC, Wallet

            rpc = RPC(self.node_url)
            wallet = Wallet(rpc, seed=self._seed, index=0)
            # bananopie expects whole BAN (it calls whole_to_raw internally)
            ban_str = (
                str(amount_ban) if amount_ban is not None else str(self.raw_to_ban(amount_raw))
            )
            result = wallet.send(to=to_address, amount=ban_str)
            return result.get("hash") if isinstance(result, dict) else None
        data = self._post(
            {
                "action": "send",
                "wallet": source_wallet,
                "destination": to_address,
                "amount": amount_raw,
            }
        )
        return data.get("block")

    def has_min_balance(self, min_ban: float, operator_account: str | None = None) -> bool:
        """Return True if operator has at least min_ban available.

        In dry_run: assume a healthy balance of 100 BAN.
        In real mode: requires operator_account and queries node RPC (account_balance).
        """
        if self.dry_run:
            return min_ban <= _DRYRUN_BALANCE_BAN
        if not operator_account:
            return False
        bal, _pending = self.account_balance(operator_account)
        return bal >= min_ban
