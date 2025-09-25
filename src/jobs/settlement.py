from __future__ import annotations

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
