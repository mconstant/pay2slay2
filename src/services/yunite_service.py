from __future__ import annotations

from http import HTTPStatus

import httpx

from src.lib.observability import instrument_http_call


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
        client = self.http
        assert client is not None
        headers: dict[str, str] = {"Authorization": f"Bot {self.api_key}"}
        url = f"{self.base_url}/v3/guilds/{self.guild_id}/members/{discord_user_id}"

        def _do(url: str = url, headers: dict[str, str] = headers) -> httpx.Response:
            return client.get(url, headers=headers)

        resp = instrument_http_call(
            "yunite.get_member",
            _do,
            attrs={
                "http.url": url,
                "http.method": "GET",
                "service.component": "yunite",
                "discord.user_id": discord_user_id,
            },
        )
        if resp.status_code == HTTPStatus.NOT_FOUND:
            return None
        resp.raise_for_status()
        data = resp.json() or {}
        # The actual field name depends on Yunite API; placeholder 'epicAccountId'
        return data.get("epicAccountId")
