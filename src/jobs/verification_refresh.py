"""Verification refresh job (T031).

Periodically re-fetch Epic account IDs for users whose epic_account_id is NULL
or whose last verification record is stale. This helps converge late Yunite
syncs or users who linked Discord after initial registration.

Design:
- Select up to batch_size users with epic_account_id IS NULL.
- For each, call YuniteService.get_epic_id_for_discord; if found, update user
  and insert a VerificationRecord row.
- Commit once at end for efficiency (small batch) or per user if needed later.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.lib.config import get_config
from src.models.models import User, VerificationRecord
from src.services.yunite_service import YuniteService


@dataclass
class VerificationRefreshConfig:
    batch_size: int | None = 50
    dry_run: bool = True


def _candidate_users(session: Session, cfg: VerificationRefreshConfig) -> Iterable[User]:
    q = select(User).where(User.epic_account_id.is_(None))
    if cfg.batch_size:
        q = q.limit(cfg.batch_size)
    return session.execute(q).scalars()


def run_verification_refresh(session: Session, cfg: VerificationRefreshConfig) -> dict[str, int]:
    cfg_obj = get_config()
    integrations = cfg_obj.integrations
    yunite = YuniteService(
        api_key=integrations.yunite_api_key,
        guild_id=integrations.yunite_guild_id,
        dry_run=integrations.dry_run,
    )
    counters = {"candidates": 0, "updated": 0}
    for user in _candidate_users(session, cfg):
        counters["candidates"] += 1
        epic_id = yunite.get_epic_id_for_discord(user.discord_user_id)
        if not epic_id:
            continue
        user.epic_account_id = epic_id
        vr = VerificationRecord(
            user_id=user.id,
            discord_user_id=user.discord_user_id,
            discord_guild_member=user.discord_guild_member,
            epic_account_id=epic_id,
            source="verification_refresh",
            status="ok",
            detail=None,
        )
        session.add(vr)
        counters["updated"] += 1
    session.commit()
    return counters


__all__ = ["VerificationRefreshConfig", "run_verification_refresh"]
