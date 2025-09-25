from collections.abc import Generator

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.lib.auth import issue_admin_session, session_secret, verify_admin_session
from src.models.models import AdminUser, Payout, User

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
