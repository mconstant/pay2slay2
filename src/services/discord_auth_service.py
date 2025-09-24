from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DiscordUser:
    user_id: str
    username: str
    guild_member: bool


class DiscordAuthService:
    """Stub for Discord OAuth and guild membership checks."""

    def exchange_code_for_user(self, code: str, redirect_uri: str) -> DiscordUser:
        # TODO: call Discord OAuth2 API. For now return a dummy user.
        return DiscordUser(user_id="0", username="stub", guild_member=False)

    def is_guild_member(self, user_id: str) -> bool:
        # TODO: query guild membership via Discord API
        return False
