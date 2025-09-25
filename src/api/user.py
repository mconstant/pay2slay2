from collections.abc import Generator

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.lib.auth import session_secret, verify_session
from src.models.models import User, VerificationRecord, WalletLink

router = APIRouter()


def _get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@router.post("/link/wallet")
def link_wallet(
    banano_address: str = Body(..., embed=True),
    request: Request = None,  # type: ignore[assignment]
    db: Session = Depends(_get_db),  # noqa: B008 - FastAPI dependency
) -> JSONResponse:
    # rudimentary validation: must start with 'ban_'
    if not isinstance(banano_address, str) or not banano_address.startswith("ban_"):
        raise HTTPException(status_code=400, detail="Invalid Banano address")
    # Identify user from session cookie
    token = request.cookies.get("p2s_session") if request else None
    uid = verify_session(token, session_secret()) if token else None
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(User).filter(User.discord_user_id == uid).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Upsert primary wallet link
    existing = (
        db.query(WalletLink)
        .filter(WalletLink.user_id == user.id, WalletLink.address == banano_address)
        .one_or_none()
    )
    if existing:
        wl = existing
    else:
        wl = WalletLink(user_id=user.id, address=banano_address, is_primary=True, verified=True)
        db.add(wl)
    db.commit()
    return JSONResponse({"linked": True, "address": banano_address})


@router.get("/me/status")
def me_status(request: Request = None, db: Session = Depends(_get_db)) -> JSONResponse:  # type: ignore[assignment]  # noqa: B008
    token = request.cookies.get("p2s_session") if request else None
    uid = verify_session(token, session_secret()) if token else None
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(User).filter(User.discord_user_id == uid).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # compute accrued rewards sum
    total_accrued = sum(float(a.amount_ban) for a in user.accruals)
    # latest verification timestamp
    latest_ver = (
        db.query(VerificationRecord)
        .filter(VerificationRecord.user_id == user.id)
        .order_by(VerificationRecord.created_at.desc())
        .first()
    )
    last_verified_at = latest_ver.created_at.isoformat() if latest_ver and latest_ver.created_at else None
    last_verified_status = latest_ver.status if latest_ver else None
    last_verified_source = latest_ver.source if latest_ver else None
    return JSONResponse(
        {
            "linked": bool(user.wallet_links),
            "last_verified_at": last_verified_at,
            "last_verified_status": last_verified_status,
            "last_verified_source": last_verified_source,
            "accrued_rewards_ban": total_accrued,
        }
    )
