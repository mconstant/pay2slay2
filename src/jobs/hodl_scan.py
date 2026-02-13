"""Periodic HODL balance scanner (runs in the scheduler loop).

Iterates users who have a Solana wallet linked and re-fetches their
on-chain $JPMT balance, updating jpmt_balance and jpmt_verified_at so
the boost tier stays current without requiring manual re-verification.
"""

from __future__ import annotations

from datetime import UTC, datetime

from prometheus_client import Counter
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.lib.config import PayoutConfig, get_config
from src.lib.observability import get_logger, get_tracer
from src.models.models import User
from src.services.domain.hodl_boost_service import (
    fetch_spl_token_balance,
    get_tier_for_balance,
)

log = get_logger("hodl_scan")

METRIC_HODL_SCANNED = Counter("hodl_scan_users_total", "Users scanned for HODL balance")
METRIC_HODL_UPDATED = Counter("hodl_scan_updated_total", "Users whose HODL balance changed")


def _hodl_eligible_users(session: Session, batch_size: int | None = None) -> list[User]:
    """Return users that have a Solana wallet address set."""
    q = select(User).where(User.solana_wallet_address.is_not(None))
    if batch_size:
        q = q.limit(batch_size)
    return list(session.execute(q).scalars())


def run_hodl_scan(
    session: Session,
    payout_cfg: PayoutConfig | None = None,
    batch_size: int | None = None,
) -> dict[str, int]:
    """Scan all linked Solana wallets and refresh $JPMT balances.

    Returns counters: users_scanned, users_updated, errors.
    """
    if payout_cfg is None:
        payout_cfg = get_config().payout

    if not payout_cfg.hodl_boost_enabled:
        log.info("hodl_scan_skipped", reason="disabled")
        return {"users_scanned": 0, "users_updated": 0, "errors": 0}

    token_ca = payout_cfg.hodl_boost_token_ca
    rpc_url = payout_cfg.hodl_boost_solana_rpc

    if not token_ca:
        log.warning("hodl_scan_skipped", reason="no_token_ca")
        return {"users_scanned": 0, "users_updated": 0, "errors": 0}

    users = _hodl_eligible_users(session, batch_size)
    tracer = get_tracer("hodl_scan")

    counters = {"users_scanned": 0, "users_updated": 0, "errors": 0}

    for user in users:
        counters["users_scanned"] += 1
        wallet = user.solana_wallet_address
        if not wallet:
            continue
        try:
            with tracer.start_as_current_span(
                "hodl_balance_check",
                attributes={"user.id": user.id, "wallet": wallet[:8] + "..."},
            ):
                balance = fetch_spl_token_balance(wallet, token_ca, rpc_url)
                old_balance = user.jpmt_balance or 0
                if balance != old_balance:
                    tier = get_tier_for_balance(balance)
                    user.jpmt_balance = balance
                    user.jpmt_verified_at = datetime.now(UTC)
                    counters["users_updated"] += 1
                    log.info(
                        "hodl_balance_updated",
                        user_id=user.id,
                        old_balance=old_balance,
                        new_balance=balance,
                        tier=tier.name,
                        multiplier=tier.multiplier,
                    )
        except Exception as exc:
            counters["errors"] += 1
            log.warning("hodl_scan_user_error", user_id=user.id, error=str(exc))

    session.commit()
    METRIC_HODL_SCANNED.inc(float(counters["users_scanned"]))
    METRIC_HODL_UPDATED.inc(float(counters["users_updated"]))
    log.info("hodl_scan_complete", **counters)
    return counters


__all__ = ["run_hodl_scan"]
