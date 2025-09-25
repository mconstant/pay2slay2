from sqlalchemy.orm import Session

from src.jobs.accrual import AccrualJobConfig, run_accrual
from src.models.models import RewardAccrual, User, WalletLink
from src.services.fortnite_service import FortniteService, KillsDelta

DELTA = 5


class FixedDeltaFortnite(FortniteService):
    def __init__(self, delta: int):  # type: ignore[super-init-not-called]
        self._delta = delta
        self._cursor_base = 0
        self._dry_run = False

    def get_kills_since(self, epic_account_id: str, cursor: str | None):  # type: ignore[override]
        prev = int(cursor) if cursor and cursor.isdigit() else 0
        new_total = prev + self._delta
        return KillsDelta(
            epic_account_id=epic_account_id,
            since_cursor=cursor,
            new_cursor=str(new_total),
            kills=self._delta,
        )


def test_accrual_job_creates_accruals(db_session: Session):  # type: ignore[override]
    # Seed two users (one with wallet verified, one without -> skipped)
    u1 = User(discord_user_id="job_u1", discord_guild_member=True, epic_account_id="epic1")
    u2 = User(discord_user_id="job_u2", discord_guild_member=True, epic_account_id="epic2")
    db_session.add_all([u1, u2])
    db_session.flush()
    wl = WalletLink(user_id=u1.id, address="ban_job_u1", is_primary=True, verified=True)
    db_session.add(wl)
    db_session.commit()

    svc = FixedDeltaFortnite(delta=DELTA)
    counters = run_accrual(db_session, svc, AccrualJobConfig(batch_size=None, dry_run=False))

    assert counters["accruals_created"] >= 1
    assert counters["accruals_created"] >= 1
    accruals_u1 = db_session.query(RewardAccrual).filter(RewardAccrual.user_id == u1.id).all()
    accruals_u2 = db_session.query(RewardAccrual).filter(RewardAccrual.user_id == u2.id).all()
    # At least one accrual for verified user
    assert any(a.kills == DELTA for a in accruals_u1)
    # No accrual for unverified user
    assert not accruals_u2
