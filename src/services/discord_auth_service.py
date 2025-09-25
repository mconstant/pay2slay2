from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass
class DiscordUser:
    user_id: str
    username: str
    guild_member: bool


class DiscordAuthService:
    """Discord OAuth and guild membership checks via Discord API."""

    def __init__(  # noqa: PLR0913 - client needs several config parameters
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        guild_id: str,
        http: httpx.Client | None = None,
        base_url: str = "https://discord.com/api",
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.guild_id = guild_id
        self.http = http or httpx.Client(timeout=10)
        self.base_url = base_url.rstrip("/")

    def _token_exchange(self, code: str) -> tuple[str, str]:
        data: dict[str, str] = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = self.http.post(f"{self.base_url}/oauth2/token", data=data, headers=headers)
        resp.raise_for_status()
        tok = resp.json()
        assert isinstance(tok, dict)
        return str(tok["access_token"]), str(tok.get("token_type", "Bearer"))

    def _fetch_me(self, access_token: str, token_type: str) -> dict[str, object]:
        headers = {"Authorization": f"{token_type} {access_token}"}
        resp = self.http.get(f"{self.base_url}/users/@me", headers=headers)
        resp.raise_for_status()
        data = resp.json()
        assert isinstance(data, dict)
        return data

    def _is_member_via_user_token(self, access_token: str, token_type: str) -> bool:
        headers = {"Authorization": f"{token_type} {access_token}"}
        resp = self.http.get(f"{self.base_url}/users/@me/guilds", headers=headers)
        resp.raise_for_status()
        guilds = resp.json() or []
        return any(str(g.get("id")) == str(self.guild_id) for g in guilds)

    def exchange_code_for_user(self, code: str) -> DiscordUser:
        access_token, token_type = self._token_exchange(code)
        me = self._fetch_me(access_token, token_type)
        is_member = self._is_member_via_user_token(access_token, token_type)
        username = me.get("username", "")
        return DiscordUser(user_id=str(me["id"]), username=str(username), guild_member=is_member)

