from __future__ import annotations

from decimal import ROUND_DOWN, Decimal
from typing import Any

import httpx

_DRYRUN_BALANCE_BAN = 1_000_000.0  # Large dummy balance for dry-run safety margin

_DRYRUN_BALANCE_BAN = 100.0


class BananoClient:
    def __init__(self, node_url: str, dry_run: bool = True) -> None:
        self.node_url = node_url
        self.dry_run = dry_run
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

    def send(self, source_wallet: str, to_address: str, amount_raw: str) -> str | None:
        if self.dry_run:
            return "dryrun-tx"
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
