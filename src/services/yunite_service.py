from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any, cast

import httpx

from src.lib.observability import instrument_http_call

log = logging.getLogger(__name__)


class YuniteService:
    """Yunite API to resolve Epic account IDs from Discord users.

    Uses the Yunite v3 API: https://yunite.xyz/docs/developers/registrationdata/
    Endpoint: POST /guild/{guildId}/registration/links
    """

    def __init__(
        self,
        api_key: str,
        guild_id: str,
        base_url: str = "https://yunite.xyz/api",
        dry_run: bool = True,
    ) -> None:
        self.api_key = api_key
        self.guild_id = guild_id
        self.base_url = base_url.rstrip("/")
        self.dry_run = dry_run
        self.http = None if dry_run else httpx.Client(timeout=10)

    def _get_registration_links(self, discord_user_ids: list[str]) -> httpx.Response:
        """Query registration links for Discord users via Yunite API."""
        client = self.http
        assert client is not None
        # Yunite uses Y-Api-Token header for authentication
        headers: dict[str, str] = {
            "Y-Api-Token": self.api_key,
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/v3/guild/{self.guild_id}/registration/links"
        body: dict[str, Any] = {
            "type": "DISCORD",
            "userIds": discord_user_ids,
        }

        def _do() -> httpx.Response:
            return client.post(url, headers=headers, json=body)

        return cast(
            httpx.Response,
            instrument_http_call(
                "yunite.get_registration_links",
                _do,
                attrs={
                    "http.url": url,
                    "http.method": "POST",
                    "service.component": "yunite",
                    "discord.user_ids": ",".join(discord_user_ids),
                },
            ),
        )

    def get_member_debug(self, discord_user_id: str) -> dict[str, Any]:
        """Debug method that returns full API response info."""
        if self.dry_run:
            return {
                "dry_run": True,
                "epic_id": f"epic_{discord_user_id}",
            }
        resp = self._get_registration_links([discord_user_id])
        try:
            body = resp.json() if resp.status_code == HTTPStatus.OK else resp.text
        except Exception:
            body = resp.text
        return {
            "status_code": resp.status_code,
            "url": str(resp.url),
            "body": body,
            "config": {
                "guild_id": self.guild_id,
                "base_url": self.base_url,
            },
        }

    def get_epic_id_for_discord(self, discord_user_id: str) -> str | None:
        """Get Epic account ID for a Discord user, or None if not found."""
        if self.dry_run:
            # Deterministic fake mapping for tests
            return f"epic_{discord_user_id}"
        resp = self._get_registration_links([discord_user_id])
        if resp.status_code == HTTPStatus.NOT_FOUND:
            return None
        resp.raise_for_status()
        data = resp.json()

        # Yunite API response format:
        # {"users": [{"discord": {"id": "..."}, "epic": {"epicID": "..."}}], "notLinked": [], "notFound": []}
        if not isinstance(data, dict):
            log.warning("Yunite unexpected response format: %s, data: %s", type(data), data)
            return None

        # Check if user is in notLinked or notFound
        not_linked = data.get("notLinked", [])
        not_found = data.get("notFound", [])
        if discord_user_id in not_linked or discord_user_id in not_found:
            return None

        # Find user in users array
        users = data.get("users", [])
        for user in users:
            discord_info = user.get("discord", {})
            if discord_info.get("id") == discord_user_id:
                epic_info = user.get("epic", {})
                epic_id: str | None = epic_info.get("epicID") or epic_info.get("epicId")
                return epic_id

        # User not found in response
        return None
