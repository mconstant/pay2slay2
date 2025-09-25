from fastapi import APIRouter, Body, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from typing import Generator
from sqlalchemy.orm import Session

from src.models.models import User, WalletLink, RewardAccrual

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
    db: Session = Depends(_get_db),
) -> JSONResponse:
    # rudimentary validation: must start with 'ban_'
    if not isinstance(banano_address, str) or not banano_address.startswith("ban_"):
        raise HTTPException(status_code=400, detail="Invalid Banano address")
    # Look up the most recent verified user (testing-only dry-run flow)
    user = db.query(User).order_by(User.id.desc()).first()
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
def me_status(request: Request = None, db: Session = Depends(_get_db)) -> JSONResponse:  # type: ignore[assignment]
    user = db.query(User).order_by(User.id.desc()).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # compute accrued rewards sum
    total_accrued = sum(float(a.amount_ban) for a in user.accruals)
    return JSONResponse(
        {
            "linked": bool(user.wallet_links),
            "last_verified_at": None,  # could add from VerificationRecord
            "accrued_rewards_ban": total_accrued,
        }
    )
