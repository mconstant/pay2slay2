import json
import os
import time as _time
from collections.abc import Generator
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.models import Payout, RewardAccrual, User
from src.services.domain.hodl_boost_service import get_tier_for_balance

router = APIRouter()


def _get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@router.get("/api/leaderboard")
def leaderboard(
    db: Session = Depends(_get_db),  # noqa: B008
    limit: int = 50,
    offset: int = 0,
) -> JSONResponse:
    """Public leaderboard showing all players, kills, and payouts. No auth required."""
    limit = min(max(limit, 1), 100)

    accrual_sub = (
        db.query(
            RewardAccrual.user_id,
            func.coalesce(func.sum(RewardAccrual.kills), 0).label("total_kills"),
            func.coalesce(func.sum(RewardAccrual.amount_ban), 0).label("total_accrued"),
        )
        .group_by(RewardAccrual.user_id)
        .subquery()
    )

    payout_sub = (
        db.query(
            Payout.user_id,
            func.coalesce(func.sum(Payout.amount_ban), 0).label("total_paid"),
        )
        .filter(Payout.status == "sent")
        .group_by(Payout.user_id)
        .subquery()
    )

    rows = (
        db.query(
            User.discord_username,
            User.jpmt_balance,
            func.coalesce(accrual_sub.c.total_kills, 0).label("total_kills"),
            func.coalesce(accrual_sub.c.total_accrued, 0).label("total_accrued"),
            func.coalesce(payout_sub.c.total_paid, 0).label("total_paid"),
        )
        .outerjoin(accrual_sub, accrual_sub.c.user_id == User.id)
        .outerjoin(payout_sub, payout_sub.c.user_id == User.id)
        .order_by(func.coalesce(accrual_sub.c.total_kills, 0).desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    total_users = db.query(func.count(User.id)).scalar() or 0

    return JSONResponse(
        {
            "players": [
                {
                    "discord_username": r.discord_username or "Unknown",
                    "total_kills": int(r.total_kills),
                    "total_accrued_ban": float(r.total_accrued),
                    "total_paid_ban": float(r.total_paid),
                    "jpmt_badge": get_tier_for_balance(r.jpmt_balance or 0).badge,
                }
                for r in rows
            ],
            "total": total_users,
            "limit": limit,
            "offset": offset,
        }
    )


@router.get("/api/feed")
def activity_feed(
    db: Session = Depends(_get_db),  # noqa: B008
    limit: int = 30,
) -> JSONResponse:
    """Public activity feed — recent accruals and payouts across all players."""
    limit = min(max(limit, 1), 100)

    accruals = (
        db.query(
            User.discord_username,
            User.jpmt_balance,
            RewardAccrual.kills,
            RewardAccrual.amount_ban,
            RewardAccrual.settled,
            RewardAccrual.created_at,
        )
        .join(User, User.id == RewardAccrual.user_id)
        .order_by(RewardAccrual.created_at.desc())
        .limit(limit)
        .all()
    )

    payouts = (
        db.query(
            User.discord_username,
            User.jpmt_balance,
            Payout.amount_ban,
            Payout.status,
            Payout.tx_hash,
            Payout.error_detail,
            Payout.created_at,
        )
        .join(User, User.id == Payout.user_id)
        .order_by(Payout.created_at.desc())
        .limit(limit)
        .all()
    )

    return JSONResponse(
        {
            "accruals": [
                {
                    "discord_username": a.discord_username or "Unknown",
                    "kills": a.kills,
                    "amount_ban": float(a.amount_ban),
                    "settled": a.settled,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "jpmt_badge": get_tier_for_balance(a.jpmt_balance or 0).badge,
                }
                for a in accruals
            ],
            "payouts": [
                {
                    "discord_username": p.discord_username or "Unknown",
                    "amount_ban": float(p.amount_ban),
                    "status": p.status,
                    "tx_hash": p.tx_hash,
                    "error_detail": p.error_detail,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "jpmt_badge": get_tier_for_balance(p.jpmt_balance or 0).badge,
                }
                for p in payouts
            ],
        }
    )


@router.get("/api/donate-info")
def donate_info(
    request: Request,
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    """Public endpoint returning operator wallet address and balance for donations."""
    operator_account = os.getenv("P2S_OPERATOR_ACCOUNT", "")

    # If no env var, try to derive from stored seed
    if not operator_account:
        from src.lib.crypto import decrypt_value
        from src.models.models import SecureConfig
        from src.services.banano_client import seed_to_address

        seed_config = (
            db.query(SecureConfig).filter(SecureConfig.key == "operator_seed").one_or_none()
        )
        if seed_config:
            decrypted = decrypt_value(seed_config.encrypted_value)
            if decrypted:
                operator_account = seed_to_address(decrypted) or ""

    if not operator_account:
        return JSONResponse({"address": None, "balance": None, "pending": None})

    balance: float | None = None
    pending: float | None = None
    app_state = getattr(request.app, "state", None)
    cfg_obj = getattr(app_state, "config", None)
    integrations = getattr(cfg_obj, "integrations", None)
    if integrations:
        try:
            from src.services.banano_client import BananoClient

            # Load operator seed so we can auto-receive pending donations
            seed_hex: str | None = None
            from src.lib.crypto import decrypt_value as _dv
            from src.models.models import SecureConfig

            _seed_row = (
                db.query(SecureConfig).filter(SecureConfig.key == "operator_seed").one_or_none()
            )
            if _seed_row:
                seed_hex = _dv(_seed_row.encrypted_value)

            banano = BananoClient(
                node_url=integrations.node_rpc,
                dry_run=integrations.dry_run,
                seed=seed_hex,
            )

            # Capture pending blocks with sender info BEFORE receiving
            pending_blocks = banano.get_receivable_blocks(operator_account)

            # Auto-receive any pending blocks before checking balance
            received_blocks = banano.receive_all_pending(account=operator_account)

            balance, pending = banano.account_balance(operator_account)

            # Record individual donations with sender addresses
            if received_blocks and pending_blocks:
                from decimal import Decimal

                from src.services.domain.donation_service import record_donation

                for block in pending_blocks:
                    amount = Decimal(str(block["amount_ban"]))
                    if amount > 0:
                        record_donation(
                            db,
                            amount_ban=amount,
                            blocks_received=1,
                            source="donate-info",
                            sender_address=block.get("sender"),
                        )
                db.commit()
        except Exception:
            pass

    return JSONResponse({"address": operator_account, "balance": balance, "pending": pending})


@router.get("/api/scheduler/countdown")
def scheduler_countdown() -> JSONResponse:
    """Public endpoint returning seconds until next accrual and settlement cycles."""
    hb_path = Path(os.getenv("P2S_HEARTBEAT_FILE", "/tmp/scheduler_heartbeat.json"))
    empty = {
        "next_accrual_in": None,
        "next_settlement_in": None,
        "accrual_interval_seconds": None,
        "settlement_interval_seconds": None,
    }
    if not hb_path.exists():
        return JSONResponse(empty)
    try:
        data = json.loads(hb_path.read_text())
        now = _time.time()
        default_interval = int(os.getenv("P2S_INTERVAL_SECONDS", "1200"))

        accrual_interval = data.get("accrual_interval_seconds") or default_interval
        settlement_interval = data.get("settlement_interval_seconds") or default_interval

        last_accrual = data.get("last_accrual_ts") or data.get("ts", 0)
        last_settlement = data.get("last_settlement_ts") or data.get("ts", 0)

        return JSONResponse(
            {
                "next_accrual_in": max(0, int(last_accrual + accrual_interval - now)),
                "next_settlement_in": max(0, int(last_settlement + settlement_interval - now)),
                "accrual_interval_seconds": accrual_interval,
                "settlement_interval_seconds": settlement_interval,
            }
        )
    except Exception:
        return JSONResponse(empty)
