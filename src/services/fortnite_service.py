from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KillsDelta:
    epic_account_id: str
    since_cursor: str | None
    new_cursor: str | None
    kills: int


class FortniteService:
    """Stub for Fortnite API integration."""

    def get_kills_since(self, epic_account_id: str, cursor: str | None) -> KillsDelta:
        # TODO: Implement real call with rate limiting and retries
        return KillsDelta(epic_account_id=epic_account_id, since_cursor=cursor, new_cursor=cursor, kills=0)
