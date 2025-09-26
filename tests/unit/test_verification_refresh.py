from __future__ import annotations

from sqlalchemy.orm import Session

from src.jobs.verification_refresh import (
    VerificationRefreshConfig,
    run_verification_refresh,
)
from src.models.models import User


def test_verification_refresh_updates_missing_epic(db_session: Session):  # type: ignore[override]
    u = User(discord_user_id="vr_user", discord_guild_member=True, epic_account_id=None)
    db_session.add(u)
    db_session.commit()
    cfg = VerificationRefreshConfig(batch_size=10, dry_run=True)
    res = run_verification_refresh(db_session, cfg)
    # Accept 1 or more candidates in case other seed logic creates additional rows
    assert res["candidates"] >= 1
    db_session.refresh(u)
    assert u.epic_account_id == "epic_vr_user"
