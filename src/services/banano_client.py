from __future__ import annotations

import httpx

_DRYRUN_BALANCE_BAN = 100.0


class BananoClient:
    def __init__(self, node_url: str, dry_run: bool = True) -> None:
        self.node_url = node_url
        self.dry_run = dry_run
        self.http = None if dry_run else httpx.Client(timeout=10)

    def send(self, source_wallet: str, to_address: str, amount_raw: str) -> str | None:
        if self.dry_run:
            return "dryrun-tx"
        assert self.http is not None
        payload = {
            "action": "send",
            "wallet": source_wallet,
            "destination": to_address,
            "amount": amount_raw,
        }
        resp = self.http.post(self.node_url, json=payload)
        resp.raise_for_status()
        data = resp.json() or {}
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
        assert self.http is not None
        payload = {"action": "account_balance", "account": operator_account}
        resp = self.http.post(self.node_url, json=payload)
        resp.raise_for_status()
        data = resp.json() or {}
        # Banano raw to BAN: 10^29 raw = 1 BAN (same as Nano scale)
        try:
            raw = int(data.get("balance", "0"))
        except ValueError:
            raw = 0
        ban = raw / (10**29)
        return ban >= min_ban
