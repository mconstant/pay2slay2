from collections.abc import Generator

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.models.models import Payout, User

router = APIRouter(prefix="/admin")


def _get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def _require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    # Simple header-based admin auth; replace with real admin auth later
    if not x_admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/reverify")
def admin_reverify(
    discord_id: str = Body(..., embed=True),
    _: None = Depends(_require_admin),
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    # Minimal stub: check user exists and return accepted; real reverify job TBD
    user = db.query(User).filter(User.discord_user_id == discord_id).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse({"status": "accepted", "discord_id": discord_id})


@router.post("/payouts/retry")
def admin_payouts_retry(
    payout_id: int = Body(..., embed=True),
    _: None = Depends(_require_admin),
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    # Minimal stub: ensure payout exists; real retry to be implemented
    payout = db.query(Payout).filter(Payout.id == payout_id).one_or_none()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    return JSONResponse({"status": "accepted", "payout_id": payout_id})
