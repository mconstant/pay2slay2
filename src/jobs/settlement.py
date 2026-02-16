from __future__ import annotations

import signal
import threading
import types
from collections.abc import Callable
from dataclasses import dataclass

from prometheus_client import Counter
from sqlalchemy.orm import Session

from src.lib.observability import get_logger
from src.services.banano_client import BananoClient
from src.services.domain.abuse_analytics_service import AbuseAnalyticsService
from src.services.domain.payout_service import PayoutService
from src.services.domain.settlement_service import SettlementService

_settle_log = get_logger("jobs.settlement")


def repair_orphaned_accruals(session: Session) -> int:
    """Un-settle accruals that were marked settled but have no linked payout.

    This can happen when daily/weekly caps reduce the payable amount but all
    accruals were still marked settled.  Resetting them lets the next settlement
    cycle create a proper payout.
    """
    from src.models.models import RewardAccrual

    orphans = (
        session.query(RewardAccrual)
        .filter(RewardAccrual.settled.is_(True), RewardAccrual.payout_id.is_(None))
        .all()
    )
    count = len(orphans)
    for a in orphans:
        a.settled = False
        a.settled_at = None
    if count:
        session.commit()
        _settle_log.info("repaired_orphaned_accruals", count=count)
    return count


@dataclass
class SchedulerConfig:
    min_operator_balance_ban: float
    batch_size: int | None
    daily_cap: int
    weekly_cap: int
    dry_run: bool
    interval_seconds: int = 15  # default 20 minutes
    operator_account: str | None = None
    node_url: str = ""  # Banano node RPC endpoint


def _load_operator_seed(session: Session) -> str | None:
    """Load the operator wallet seed from SecureConfig (encrypted at rest)."""
    from src.lib.crypto import decrypt_value
    from src.models.models import SecureConfig

    row = session.query(SecureConfig).filter(SecureConfig.key == "operator_seed").one_or_none()
    if not row:
        return None
    return decrypt_value(row.encrypted_value)


def run_settlement(session: Session, cfg: SchedulerConfig) -> dict[str, int]:
    """Select candidates and create payouts; returns simple counters.

    Note: caps and operator balance checks to be fleshed out in later tasks.
    """
    # Repair any accruals orphaned by the old settle-all-even-when-capped bug
    repair_orphaned_accruals(session)

    settlement = SettlementService(session, daily_cap=cfg.daily_cap, weekly_cap=cfg.weekly_cap)
    seed = _load_operator_seed(session)
    banano = BananoClient(node_url=cfg.node_url, dry_run=cfg.dry_run, seed=seed)
    payout_svc = PayoutService(session, banano=banano, dry_run=cfg.dry_run)

    counters = {"candidates": 0, "payouts": 0, "accruals_settled": 0}
    candidates = settlement.select_candidates(limit=cfg.batch_size)
    counters["candidates"] = len(candidates)
    analytics = AbuseAnalyticsService()
    for cand in candidates:
        payable_amt = (
            cand.payable_amount_ban
            if hasattr(cand, "payable_amount_ban")
            else cand.total_amount_ban
        )
        payable_kills = cand.payable_kills if hasattr(cand, "payable_kills") else cand.total_kills
        if not payable_amt or not payable_kills:
            continue
        # collect unsettled accruals for this user
        all_unsettled = [a for a in cand.user.accruals if not a.settled]
        if not all_unsettled:
            continue
        # Only settle accruals up to the payable kill count (caps may reduce it).
        # Sort oldest-first so earlier accruals get settled before newer ones.
        all_unsettled.sort(key=lambda a: a.created_at or a.id)
        accruals = []
        kills_budget = payable_kills
        for a in all_unsettled:
            if kills_budget <= 0:
                break
            accruals.append(a)
            kills_budget -= a.kills
        if not accruals:
            continue
        res = payout_svc.create_payout(cand.user, payable_amt, accruals)
        if res:
            counters["payouts"] += 1
            counters["accruals_settled"] += len(accruals)
            # Record payout by region (user.region_code may be None)
            region = getattr(cand.user, "region_code", None)
            analytics.record_payout(region)
    session.commit()
    # Export metrics
    METRIC_CANDIDATES.inc(float(counters["candidates"]))
    METRIC_PAYOUTS.inc(float(counters["payouts"]))
    METRIC_ACCRUALS_SETTLED.inc(float(counters["accruals_settled"]))
    return counters


# Prometheus counters
METRIC_CANDIDATES = Counter(
    "settlement_candidates_total", "Number of candidates considered per run"
)
METRIC_PAYOUTS = Counter("settlement_payouts_total", "Number of payouts created per run")
METRIC_ACCRUALS_SETTLED = Counter(
    "settlement_accruals_settled_total", "Number of accrual records settled per run"
)


def run_scheduler(
    session_factory: Callable[[], Session],
    cfg: SchedulerConfig,
    stop_event: threading.Event | None = None,
) -> None:
    """Blocking loop that runs settlement on an interval with operator balance check.

    Intended to be started in a background process/task runner. Safe for dry_run.
    """
    local_event = stop_event or threading.Event()

    def _signal_handler(signum: int, frame: types.FrameType | None) -> None:
        # Set the event to stop the loop gracefully
        local_event.set()

    # Register signal handlers for graceful shutdown
    prev_int = signal.signal(signal.SIGINT, _signal_handler)
    prev_term = signal.signal(signal.SIGTERM, _signal_handler)
    try:
        while not local_event.is_set():
            session: Session = session_factory()
            try:
                banano = BananoClient(node_url=cfg.node_url, dry_run=cfg.dry_run)
                if not banano.has_min_balance(cfg.min_operator_balance_ban, cfg.operator_account):
                    # Insufficient operator funds; skip this cycle
                    local_event.wait(cfg.interval_seconds)
                else:
                    run_settlement(session, cfg)
            finally:
                session.close()
            # Wait for interval or until stop requested
            local_event.wait(cfg.interval_seconds)
    finally:
        # Restore previous handlers
        signal.signal(signal.SIGINT, prev_int)
        signal.signal(signal.SIGTERM, prev_term)
