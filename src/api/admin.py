import os
from collections.abc import Generator
from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from prometheus_client import Counter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.lib.admin_audit import AdminAuditPayload, record_admin_audit
from src.lib.auth import issue_admin_session, session_secret, verify_admin_session
from src.lib.observability import get_logger
from src.models.models import (
    AbuseFlag,
    AdminAudit,
    AdminUser,
    Payout,
    RewardAccrual,
    User,
    VerificationRecord,
)
from src.services.banano_client import BananoClient
from src.services.yunite_service import YuniteService

router = APIRouter(prefix="/admin")
log = get_logger("api.admin")

# Admin metrics
ADMIN_REVERIFY_TOTAL = Counter("admin_reverify_total", "Admin reverify requests", ["result"])
ADMIN_PAYOUT_RETRY_TOTAL = Counter(
    "admin_payout_retry_total", "Admin payout retry attempts", ["result"]
)


def _get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def _require_admin(request: Request) -> None:
    token = request.cookies.get("p2s_admin")
    email = verify_admin_session(token, session_secret()) if token else None
    if not email:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/login")
def admin_login(email: str = Body(..., embed=True), db: Session = Depends(_get_db)) -> JSONResponse:  # noqa: B008
    # Simple login: require active AdminUser with this email, then issue admin cookie
    if not email:
        raise HTTPException(status_code=400, detail="email required")
    admin = (
        db.query(AdminUser)
        .filter(AdminUser.email == email, AdminUser.is_active.is_(True))
        .one_or_none()
    )

    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = issue_admin_session(email, session_secret())
    resp = JSONResponse({"email": email})
    resp.set_cookie("p2s_admin", token, httponly=True, samesite="lax")
    record_admin_audit(
        db,
        AdminAuditPayload(
            action="admin_login",
            actor_email=email,
            target_type="admin_user",
            target_id=email,
            summary="login",
        ),
    )
    db.commit()
    log.info("admin_login", email=email)
    return resp


@router.post("/reverify")
def admin_reverify(
    request: Request,
    discord_id: str = Body(..., embed=True),
    _: None = Depends(_require_admin),
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    user = db.query(User).filter(User.discord_user_id == discord_id).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Build Yunite service from app config
    app_state = getattr(getattr(request, "app", None), "state", None)
    cfg_obj = getattr(app_state, "config", None)
    integrations = getattr(cfg_obj, "integrations", None)
    if integrations is None:
        raise HTTPException(status_code=500, detail="Config not loaded")
    yunite = YuniteService(
        api_key=integrations.yunite_api_key,
        guild_id=integrations.yunite_guild_id,
        dry_run=integrations.dry_run,
    )
    epic_id = yunite.get_epic_id_for_discord(discord_id)
    user.epic_account_id = epic_id
    # Do not change guild membership here; separate Discord check would be needed
    vr = VerificationRecord(
        user_id=user.id,
        discord_user_id=user.discord_user_id,
        discord_guild_member=user.discord_guild_member,
        epic_account_id=epic_id,
        source="admin_reverify",
        status="ok",
        detail=None,
    )
    db.add(vr)
    db.commit()
    record_admin_audit(
        db,
        AdminAuditPayload(
            action="admin_reverify",
            actor_email=None,
            target_type="user",
            target_id=discord_id,
            summary="reverify",
        ),
    )
    db.commit()
    log.info("admin_reverify", discord_id=discord_id, epic_account_id=epic_id)
    ADMIN_REVERIFY_TOTAL.labels(result="accepted").inc()
    return JSONResponse(
        {"status": "accepted", "discord_id": discord_id, "epic_account_id": epic_id}
    )


@router.post("/payouts/retry")
def admin_payouts_retry(
    request: Request,
    payout_id: int = Body(..., embed=True),
    _: None = Depends(_require_admin),
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    payout = db.query(Payout).filter(Payout.id == payout_id).one_or_none()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    # Idempotency: if already has tx_hash and status sent, return success quickly
    if payout.tx_hash and payout.status == "sent":
        ADMIN_PAYOUT_RETRY_TOTAL.labels(result="already_sent").inc()
        log.info("admin_payout_retry_already_sent", payout_id=payout_id, tx_hash=payout.tx_hash)
        return JSONResponse(
            {"status": "already_sent", "payout_id": payout_id, "tx_hash": payout.tx_hash}
        )
    # Attempt resend using configured node
    app_state = getattr(getattr(request, "app", None), "state", None)
    cfg_obj = getattr(app_state, "config", None)
    integrations = getattr(cfg_obj, "integrations", None)
    if integrations is None:
        raise HTTPException(status_code=500, detail="Config not loaded")
    banano = BananoClient(node_url=integrations.node_rpc, dry_run=integrations.dry_run)
    source_wallet = os.getenv("P2S_OPERATOR_WALLET", "operator")
    amount_raw = str(float(payout.amount_ban))
    tx = banano.send(source_wallet=source_wallet, to_address=payout.address, amount_raw=amount_raw)
    if tx:
        payout.tx_hash = tx
        payout.status = "sent"
        payout.error_detail = None
        ADMIN_PAYOUT_RETRY_TOTAL.labels(result="sent").inc()
        log.info("admin_payout_retry_sent", payout_id=payout_id, tx_hash=tx)
    else:
        payout.status = "failed"
        payout.error_detail = payout.error_detail or "retry failed"
        ADMIN_PAYOUT_RETRY_TOTAL.labels(result="failed").inc()
        log.warning("admin_payout_retry_failed", payout_id=payout_id)
    record_admin_audit(
        db,
        AdminAuditPayload(
            action="admin_payout_retry",
            actor_email=None,
            target_type="payout",
            target_id=str(payout_id),
            summary=payout.status,
            detail=payout.error_detail,
        ),
    )
    db.commit()
    return JSONResponse(
        {"status": payout.status, "payout_id": payout_id, "tx_hash": payout.tx_hash}
    )


@router.get("/audit")
def admin_audit_query(  # noqa: PLR0913 - explicit filter params acceptable here
    request: Request,
    action: str | None = None,
    actor_email: str | None = None,
    target_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    _: None = Depends(_require_admin),
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    """Query admin audit events with optional filters."""
    limit = min(max(limit, 1), 200)
    stmt = select(AdminAudit).order_by(AdminAudit.created_at.desc()).offset(offset).limit(limit)
    if action:
        stmt = stmt.filter(AdminAudit.action == action)
    if actor_email:
        stmt = stmt.filter(AdminAudit.actor_email == actor_email)
    if target_type:
        stmt = stmt.filter(AdminAudit.target_type == target_type)
    rows = db.execute(stmt).scalars().all()
    return JSONResponse(
        {
            "count": len(rows),
            "limit": limit,
            "offset": offset,
            "events": [
                {
                    "id": r.id,
                    "created_at": r.created_at.isoformat()
                    if getattr(r, "created_at", None)
                    else None,
                    "action": r.action,
                    "actor_email": r.actor_email,
                    "target_type": r.target_type,
                    "target_id": r.target_id,
                    "summary": r.summary,
                }
                for r in rows
            ],
        }
    )


@router.get("/stats")
def admin_stats(
    _: None = Depends(_require_admin),
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    """Aggregate system statistics for dashboards (fast COUNT/SUM queries)."""
    user_count = db.query(func.count(User.id)).scalar() or 0
    verifications_ok = (
        db.query(func.count(VerificationRecord.id))
        .filter(VerificationRecord.status == "ok")
        .scalar()
        or 0
    )
    payouts_sent_sum = (
        db.query(func.coalesce(func.sum(Payout.amount_ban), 0))
        .filter(Payout.status == "sent")
        .scalar()
        or 0
    )
    accruals_sum = db.query(func.coalesce(func.sum(RewardAccrual.amount_ban), 0)).scalar() or 0
    abuse_flags = db.query(func.count(AbuseFlag.id)).scalar() or 0
    return JSONResponse(
        {
            "users_total": user_count,
            "verifications_ok": verifications_ok,
            "payouts_sent_ban": float(payouts_sent_sum),
            "accruals_total_ban": float(accruals_sum),
            "abuse_flags": abuse_flags,
        }
    )


@router.get("/health/extended")
def admin_health_extended(request: Request, _: None = Depends(_require_admin)) -> JSONResponse:
    """Extended health with DB latency probe and uptime."""
    started_at = getattr(request.app.state, "started_at", None)
    now = datetime.now(UTC)
    uptime_sec = (now - started_at).total_seconds() if started_at else None
    session_factory = getattr(request.app.state, "session_factory", None)
    db_ok = False
    latency_ms: float | None = None
    if session_factory:
        try:  # pragma: no cover - simple probe
            import time as _t

            t0 = _t.perf_counter()
            s = session_factory()
            try:
                s.execute("SELECT 1")
                db_ok = True
            finally:
                s.close()
            latency_ms = (_t.perf_counter() - t0) * 1000.0
        except Exception:
            db_ok = False
    return JSONResponse(
        {
            "status": "ok" if db_ok else "degraded",
            "db_ok": db_ok,
            "db_latency_ms": latency_ms,
            "uptime_sec": uptime_sec,
            "config_error": getattr(request.app.state, "config_error", None),
            "db_init_error": getattr(request.app.state, "db_init_error", None),
        }
    )
