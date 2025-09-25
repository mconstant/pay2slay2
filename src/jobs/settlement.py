from __future__ import annotations

import time
from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.services.banano_client import BananoClient
from src.services.domain.payout_service import PayoutService
from src.services.domain.settlement_service import SettlementService


@dataclass
class SchedulerConfig:
    min_operator_balance_ban: float
    batch_size: int | None
    daily_cap: int
    weekly_cap: int
    dry_run: bool
    interval_seconds: int = 1200  # default 20 minutes
    operator_account: str | None = None


def run_settlement(session: Session, cfg: SchedulerConfig) -> dict[str, int]:
    """Select candidates and create payouts; returns simple counters.

    Note: caps and operator balance checks to be fleshed out in later tasks.
    """
    settlement = SettlementService(session, daily_cap=cfg.daily_cap, weekly_cap=cfg.weekly_cap)
    banano = BananoClient(node_url="", dry_run=cfg.dry_run)
    payout_svc = PayoutService(session, banano=banano, dry_run=cfg.dry_run)

    counters = {"candidates": 0, "payouts": 0, "accruals_settled": 0}
    candidates = settlement.select_candidates(limit=cfg.batch_size)
    counters["candidates"] = len(candidates)
    for cand in candidates:
        if cand.total_amount_ban <= 0 or cand.total_kills <= 0:
            continue
        # collect unsettled accruals for this user
        accruals = [a for a in cand.user.accruals if not a.settled]
        if not accruals:
            continue
        res = payout_svc.create_payout(cand.user, cand.total_amount_ban, accruals)
        if res:
            counters["payouts"] += 1
            counters["accruals_settled"] += len(accruals)
    session.commit()
    return counters


from typing import Callable


def run_scheduler(session_factory: Callable[[], Session], cfg: SchedulerConfig) -> None:
    """Blocking loop that runs settlement on an interval with operator balance check.

    Intended to be started in a background process/task runner. Safe for dry_run.
    """
    while True:
        session: Session = session_factory()
        try:
            banano = BananoClient(node_url="", dry_run=cfg.dry_run)
            if not banano.has_min_balance(cfg.min_operator_balance_ban, cfg.operator_account):
                # Insufficient operator funds; skip this cycle
                time.sleep(cfg.interval_seconds)
                continue
            run_settlement(session, cfg)
        finally:
            session.close()
        time.sleep(cfg.interval_seconds)
