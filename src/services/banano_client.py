from __future__ import annotations

import httpx


class BananoClient:
    def __init__(self, node_url: str, dry_run: bool = True) -> None:
        self.node_url = node_url
        self.dry_run = dry_run
        self.http = None if dry_run else httpx.Client(timeout=10)

    def send(self, source_wallet: str, to_address: str, amount_raw: str) -> str | None:
        if self.dry_run:
            return "dryrun-tx"
        assert self.http is not None
        payload = {"action": "send", "wallet": source_wallet, "destination": to_address, "amount": amount_raw}
        resp = self.http.post(self.node_url, json=payload)
        resp.raise_for_status()
        data = resp.json() or {}
        return data.get("block")
