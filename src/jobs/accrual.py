"""Accrual batch job (T033).

Iterates eligible users (have epic_account_id and at least one verified wallet) and
invokes AccrualService to persist RewardAccrual rows when kill deltas are positive.

Design goals:
 - Idempotent per epoch_minute (AccrualService already guards by unique constraint)
 - Lightweight counters returned for scheduler / logging / metrics integration
 - Batch size limiting for large user sets; simple offset pagination placeholder
 - Dry-run still performs accrual logic (FortniteService may be in dry_run) but we commit
   because accruals themselves are not blockchain side-effects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from prometheus_client import Counter
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.lib.config import get_config
from src.lib.observability import get_tracer
from src.models.models import User, WalletLink
from src.services.domain.accrual_service import AccrualService
from src.services.fortnite_service import FortniteService


@dataclass
class AccrualJobConfig:
    batch_size: int | None = None  # max users per run; None = all
    dry_run: bool = True
    require_verified_wallet: bool = True


# Prometheus counters
METRIC_ACCRUAL_USERS = Counter(
    "accrual_users_considered_total", "Users considered for accrual per run"
)
METRIC_ACCRUAL_CREATED = Counter("accrual_rows_created_total", "RewardAccrual rows created per run")
METRIC_ACCRUAL_ZERO = Counter("accrual_zero_delta_total", "Users with zero kill delta per run")
METRIC_ACCRUAL_KILLS = Counter(
    "accrual_kills_delta_total", "Total kill delta summed across users per run"
)


def _eligible_users(session: Session, cfg: AccrualJobConfig) -> Iterable[User]:
    """Return iterable of eligible users honoring batch size."""
    q = select(User).where(User.epic_account_id.is_not(None))
    if cfg.require_verified_wallet:
        q = (
            q.join(WalletLink, WalletLink.user_id == User.id)
            .where(WalletLink.verified.is_(True))
            .distinct()
        )
    if cfg.batch_size:
        q = q.limit(cfg.batch_size)
    return session.execute(q).scalars()


def run_accrual(
    session: Session, fortnite: FortniteService, cfg: AccrualJobConfig
) -> dict[str, int]:
    """Execute one accrual batch.

    Returns counters: users_considered, accruals_created, zero_delta, total_kills.
    """
    app_cfg = get_config()
    svc = AccrualService(
        session,
        fortnite=fortnite,
        payout_amount_per_kill=app_cfg.payout.payout_amount_ban_per_kill,
    )

    counters = {
        "users_considered": 0,
        "accruals_created": 0,
        "zero_delta": 0,
        "total_kills": 0,
    }
    tracer = get_tracer("accrual_job")
    for user in _eligible_users(session, cfg):
        counters["users_considered"] += 1
        with tracer.start_as_current_span(
            "accrue_user", attributes={"user.id": user.id, "user.discord_id": user.discord_user_id}
        ):
            res = svc.accrue_for_user(user)
        if not res:
            counters["zero_delta"] += 1
            continue
        if res.kills_delta <= 0:
            counters["zero_delta"] += 1
            continue
        counters["accruals_created"] += 1 if res.created else 0
        counters["total_kills"] += res.kills_delta

    session.commit()
    METRIC_ACCRUAL_USERS.inc(float(counters["users_considered"]))
    METRIC_ACCRUAL_CREATED.inc(float(counters["accruals_created"]))
    METRIC_ACCRUAL_ZERO.inc(float(counters["zero_delta"]))
    METRIC_ACCRUAL_KILLS.inc(float(counters["total_kills"]))
    return counters


__all__ = ["AccrualJobConfig", "run_accrual"]
