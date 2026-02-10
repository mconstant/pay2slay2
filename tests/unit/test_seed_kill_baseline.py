from __future__ import annotations

from src.services.fortnite_service import FortniteService, KillsDelta, seed_kill_baseline


class FakeFortniteService(FortniteService):
    """Stub that returns a configurable lifetime kill count."""

    def __init__(self, lifetime_kills: int = 0) -> None:
        super().__init__(api_key="fake", dry_run=True)
        self._lifetime_kills = lifetime_kills

    def get_kills_since(self, epic_account_id: str, cursor: str | None) -> KillsDelta:
        prev = int(cursor) if cursor and cursor.isdigit() else 0
        return KillsDelta(
            epic_account_id=epic_account_id,
            since_cursor=cursor,
            new_cursor=str(self._lifetime_kills),
            kills=max(self._lifetime_kills - prev, 0),
        )


def test_seed_kill_baseline_returns_lifetime_kills():
    expected_kills = 1208
    fortnite = FakeFortniteService(lifetime_kills=expected_kills)
    baseline = seed_kill_baseline(fortnite, "epic_abc")
    assert baseline == expected_kills


def test_seed_kill_baseline_zero_kills():
    fortnite = FakeFortniteService(lifetime_kills=0)
    baseline = seed_kill_baseline(fortnite, "epic_abc")
    assert baseline == 0


def test_seed_kill_baseline_dry_run_returns_zero():
    """In dry_run mode the real FortniteService returns cursor=0, so baseline is 0."""
    fortnite = FortniteService(api_key="test", dry_run=True)
    baseline = seed_kill_baseline(fortnite, "epic_abc")
    assert baseline == 0
