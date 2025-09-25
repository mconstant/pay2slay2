from __future__ import annotations

from sqlalchemy.orm import Session

from src.models.models import User
from src.services.domain.accrual_service import AccrualService
from src.services.fortnite_service import FortniteService


class StubFortnite(FortniteService):
    def __init__(self, delta: int) -> None:  # type: ignore[super-init-not-called]
        self._delta = delta

    def get_kills_since(self, epic_account_id: str, cursor: str | None):  # type: ignore[override]
        from src.services.fortnite_service import KillsDelta

        return KillsDelta(
            epic_account_id=epic_account_id,
            since_cursor=cursor,
            new_cursor=cursor,
            kills=self._delta,
        )


def test_accrual_no_epic_id(db_session: Session):
    user = User(discord_user_id="u1", discord_guild_member=True)
    db_session.add(user)
    db_session.commit()
    svc = AccrualService(db_session, fortnite=StubFortnite(delta=5), payout_amount_per_kill=2.1)
    assert svc.accrue_for_user(user) is None


def test_accrual_zero_delta(db_session: Session):
    user = User(discord_user_id="u2", discord_guild_member=True, epic_account_id="epic")
    db_session.add(user)
    db_session.commit()
    svc = AccrualService(db_session, fortnite=StubFortnite(delta=0), payout_amount_per_kill=2.1)
    res = svc.accrue_for_user(user)
    assert res is not None
    assert res.kills_delta == 0
    assert res.created is False


# Future: add test for positive delta when FortniteService implemented
