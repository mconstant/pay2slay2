from collections.abc import Generator

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.lib.auth import issue_admin_session, session_secret, verify_admin_session
from src.models.models import AdminUser, Payout, User, VerificationRecord
from src.services.banano_client import BananoClient
from src.services.yunite_service import YuniteService

router = APIRouter(prefix="/admin")


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
    admin = db.query(AdminUser).filter(AdminUser.email == email, AdminUser.is_active == True).one_or_none()  # noqa: E712
    if not admin:
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = issue_admin_session(email, session_secret())
    resp = JSONResponse({"email": email})
    resp.set_cookie("p2s_admin", token, httponly=True, samesite="lax")
    return resp

@router.post("/reverify")
def admin_reverify(
    discord_id: str = Body(..., embed=True),
    _: None = Depends(_require_admin),
    db: Session = Depends(_get_db),  # noqa: B008
    request: Request = None,  # type: ignore[assignment]
) -> JSONResponse:
    user = db.query(User).filter(User.discord_user_id == discord_id).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Deterministic dry-run: refresh Epic mapping via Yunite stub and record verification
    yunite = YuniteService(api_key="", guild_id="", dry_run=True)
    epic_id = yunite.get_epic_id_for_discord(discord_id)
    user.epic_account_id = epic_id
    # Assume still guild member in dry-run
    user.discord_guild_member = True
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
    return JSONResponse({"status": "accepted", "discord_id": discord_id, "epic_account_id": epic_id})


@router.post("/payouts/retry")
def admin_payouts_retry(
    payout_id: int = Body(..., embed=True),
    _: None = Depends(_require_admin),
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    payout = db.query(Payout).filter(Payout.id == payout_id).one_or_none()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    # Idempotency: if already has tx_hash and status sent, return success quickly
    if payout.tx_hash and payout.status == "sent":
        return JSONResponse({"status": "already_sent", "payout_id": payout_id, "tx_hash": payout.tx_hash})
    # Attempt resend (dry-run by default)
    banano = BananoClient(node_url="", dry_run=True)
    tx = banano.send(source_wallet="operator", to_address=payout.address, amount_raw=str(float(payout.amount_ban)))
    if tx:
        payout.tx_hash = tx
        payout.status = "sent"
        payout.error_detail = None
    else:
        payout.status = "failed"
        payout.error_detail = payout.error_detail or "retry failed"
    db.commit()
    return JSONResponse({"status": payout.status, "payout_id": payout_id, "tx_hash": payout.tx_hash})
