import os
from collections.abc import Generator

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from prometheus_client import Counter
from sqlalchemy.orm import Session

from src.lib.admin_audit import AdminAuditPayload, record_admin_audit
from src.lib.auth import issue_admin_session, session_secret, verify_admin_session
from src.lib.observability import get_logger
from src.models.models import AdminUser, Payout, User, VerificationRecord
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
