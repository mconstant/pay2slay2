from __future__ import annotations

from http import HTTPStatus

import httpx


class YuniteService:
    """Yunite API to resolve Epic account IDs from Discord users."""

    def __init__(
        self,
        api_key: str,
        guild_id: str,
        base_url: str = "https://api.yunite.xyz",
        dry_run: bool = True,
    ) -> None:
        self.api_key = api_key
        self.guild_id = guild_id
        self.base_url = base_url.rstrip("/")
        self.dry_run = dry_run
        self.http = None if dry_run else httpx.Client(timeout=10)

    def get_epic_id_for_discord(self, discord_user_id: str) -> str | None:
        if self.dry_run:
            # Deterministic fake mapping for tests
            return f"epic_{discord_user_id}"
        assert self.http is not None
        headers = {"Authorization": f"Bot {self.api_key}"}
        url = f"{self.base_url}/v3/guilds/{self.guild_id}/members/{discord_user_id}"
        resp = self.http.get(url, headers=headers)
        if resp.status_code == HTTPStatus.NOT_FOUND:
            return None
        resp.raise_for_status()
        data = resp.json() or {}
        # The actual field name depends on Yunite API; placeholder 'epicAccountId'
        return data.get("epicAccountId")
