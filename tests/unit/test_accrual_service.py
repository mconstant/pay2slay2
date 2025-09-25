from __future__ import annotations

from sqlalchemy.orm import Session

from src.models.models import User
from src.services.domain.accrual_service import AccrualService
from src.services.fortnite_service import FortniteService, KillsDelta

DELTA_FIVE = 5
PAYOUT_PER_KILL = 2.0
EXPECTED_AMOUNT = DELTA_FIVE * PAYOUT_PER_KILL


class StubFortnite(FortniteService):
    def __init__(self, delta: int) -> None:  # type: ignore[super-init-not-called]
        self._delta = delta

    def get_kills_since(self, epic_account_id: str, cursor: str | None):  # type: ignore[override]
        prev = int(cursor) if cursor and cursor.isdigit() else 0
        return KillsDelta(
            epic_account_id=epic_account_id,
            since_cursor=cursor,
            new_cursor=str(prev + self._delta),
            kills=self._delta,
        )


def test_accrual_no_epic_id(db_session: Session):
    user = User(discord_user_id="u1", discord_guild_member=True)
    db_session.add(user)
    db_session.commit()
    svc = AccrualService(
        db_session, fortnite=StubFortnite(delta=DELTA_FIVE), payout_amount_per_kill=2.1
    )
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


def test_accrual_positive_delta(db_session: Session):
    user = User(discord_user_id="u3", discord_guild_member=True, epic_account_id="epic")
    db_session.add(user)
    db_session.commit()
    svc = AccrualService(
        db_session, fortnite=StubFortnite(delta=DELTA_FIVE), payout_amount_per_kill=PAYOUT_PER_KILL
    )
    res = svc.accrue_for_user(user)
    assert res is not None
    assert res.kills_delta == DELTA_FIVE
    assert res.amount_ban == EXPECTED_AMOUNT
    assert res.created is True


# Future: add test for positive delta when FortniteService implemented
