from collections.abc import Generator

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.lib.auth import session_secret, verify_session
from src.models.models import Payout, User, VerificationRecord, WalletLink

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


@router.post("/me/reverify")
def me_reverify(
    request: Request | None = None,
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    token = request.cookies.get("p2s_session") if request else None
    uid = verify_session(token, session_secret()) if token else None
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(User).filter(User.discord_user_id == uid).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Access app integrations config
    app_state = getattr(getattr(request, "app", None), "state", None)
    cfg_obj = getattr(app_state, "config", None)
    integrations = getattr(cfg_obj, "integrations", None)
    if integrations is None:
        raise HTTPException(status_code=500, detail="Config not loaded")
    # Invoke Yunite to fetch latest epic id
    from src.services.yunite_service import YuniteService

    yunite = YuniteService(
        api_key=integrations.yunite_api_key,
        guild_id=integrations.yunite_guild_id,
        dry_run=integrations.dry_run,
    )
    epic_id = yunite.get_epic_id_for_discord(user.discord_user_id)
    user.epic_account_id = epic_id
    vr = VerificationRecord(
        user_id=user.id,
        discord_user_id=user.discord_user_id,
        discord_guild_member=user.discord_guild_member,
        epic_account_id=epic_id,
        source="user_reverify",
        status="ok",
        detail=None,
    )
    db.add(vr)
    db.commit()
    return JSONResponse(
        {
            "status": "accepted",
            "discord_id": user.discord_user_id,
            "epic_account_id": epic_id,
        }
    )


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
    last_verified_at = (
        latest_ver.created_at.isoformat() if latest_ver and latest_ver.created_at else None
    )
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


@router.get("/me/payouts")
def me_payouts(
    request: Request = None,  # type: ignore[assignment]
    db: Session = Depends(_get_db),  # noqa: B008
    limit: int = 20,
    offset: int = 0,
) -> JSONResponse:
    token = request.cookies.get("p2s_session") if request else None
    uid = verify_session(token, session_secret()) if token else None
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(User).filter(User.discord_user_id == uid).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    q = (
        db.query(Payout)
        .filter(Payout.user_id == user.id)
        .order_by(Payout.created_at.desc())
        .offset(offset)
        .limit(min(limit, 100))
    )
    rows = q.all()
    return JSONResponse(
        {
            "payouts": [
                {
                    "id": p.id,
                    "amount_ban": float(p.amount_ban),
                    "status": p.status,
                    "tx_hash": p.tx_hash,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in rows
            ],
            "count": len(rows),
            "limit": limit,
            "offset": offset,
        }
    )
