from __future__ import annotations

from sqlalchemy.orm import Session

from src.lib.config import get_config
from src.models.models import User
from src.services.domain.accrual_service import AccrualService
from src.services.fortnite_service import FortniteService, KillsDelta


class BurstFortnite(FortniteService):  # type: ignore[misc]
    def __init__(self, spike_kills: int):  # type: ignore[super-init-not-called]
        self.spike_kills = spike_kills
        self._served = False

    def get_kills_since(self, epic_account_id: str, cursor: str | None):  # type: ignore[override]
        if self._served:
            # subsequent -> zero
            return KillsDelta(
                epic_account_id=epic_account_id,
                since_cursor=cursor,
                new_cursor=cursor,
                kills=0,
            )
        self._served = True
        base = int(cursor) if cursor and cursor.isdigit() else 0
        new_total = base + self.spike_kills
        return KillsDelta(
            epic_account_id=epic_account_id,
            since_cursor=cursor,
            new_cursor=str(new_total),
            kills=self.spike_kills,
        )


def test_kill_rate_spike_flag(db_session: Session):  # type: ignore[override]
    cfg = get_config()
    # Lower threshold for test: ensure heuristic triggers (env abuse_heuristics.kill_rate_per_min is 10)
    user = User(
        discord_user_id="abuse_user", discord_guild_member=True, epic_account_id="epic_abuse"
    )
    db_session.add(user)
    db_session.commit()

    svc = AccrualService(
        db_session,
        BurstFortnite(
            spike_kills=cfg.integrations.abuse_heuristics.get("kill_rate_per_min", 10) + 5
        ),
        cfg.payout.payout_amount_ban_per_kill,
    )
    res = svc.accrue_for_user(user)
    assert res and res.kills_delta > 0
    # Run accrual job logic minimal subset: simulate second no-op accrual to allow evaluation path triggered in job
    from src.jobs.accrual import AccrualJobConfig, run_accrual
    from src.services.fortnite_service import FortniteService as BaseFortnite

    class StubFortnite(BaseFortnite):  # type: ignore[misc]
        def get_kills_since(self, epic_account_id: str, cursor: str | None):  # type: ignore[override]
            return KillsDelta(
                epic_account_id=epic_account_id,
                since_cursor=cursor,
                new_cursor=cursor,
                kills=0,
            )

    run_accrual(db_session, StubFortnite(), AccrualJobConfig(batch_size=None, dry_run=True))
    # Assert AbuseFlag persisted
    from src.models.models import AbuseFlag

    flags = db_session.query(AbuseFlag).filter(AbuseFlag.user_id == user.id).all()
    assert flags and flags[0].flag_type == "kill_rate_spike"
