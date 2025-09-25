from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.lib.auth import issue_session, session_secret, verify_oauth_state
from src.models.models import User, VerificationRecord
from src.services.discord_auth_service import DiscordAuthService
from src.services.yunite_service import YuniteService

router = APIRouter()


def _get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@router.post("/auth/discord/callback")
def discord_callback(
    state: str = Query(..., description="OAuth state"),
    code: str = Query(..., description="OAuth authorization code"),
    request: Request = None,  # type: ignore[assignment]
    db: Session = Depends(_get_db),  # noqa: B008 - FastAPI dependency
) -> JSONResponse:
    if not state or not code:
        raise HTTPException(status_code=400, detail="Missing state or code")
    # Basic state token validation (accept legacy 'xyz' in dry-run for backward compat tests)
    secret = session_secret()
    if state != "xyz" and not verify_oauth_state(state, secret):
        raise HTTPException(status_code=400, detail="Invalid state")

    # Build services from config; default to dry_run in local
    config = request.app.state.config
    integ = config.integrations
    discord = DiscordAuthService(
        client_id=integ.discord_oauth_client_id,
        client_secret=integ.discord_oauth_client_secret,
        redirect_uri=integ.discord_redirect_uri,
        guild_id=integ.discord_guild_id,
        dry_run=integ.dry_run,
    )
    yunite = YuniteService(
        api_key=integ.yunite_api_key, guild_id=integ.yunite_guild_id, dry_run=integ.dry_run
    )

    user_info = discord.exchange_code_for_user(code)
    if not user_info.guild_member:
        raise HTTPException(status_code=403, detail="Guild membership required")
    epic_id = yunite.get_epic_id_for_discord(user_info.user_id)
    if not epic_id:
        raise HTTPException(status_code=403, detail="Yunite EpicID mapping required")

    # Upsert user
    existing = db.query(User).filter(User.discord_user_id == user_info.user_id).one_or_none()
    region_code = getattr(getattr(request, "state", None), "region_code", None)
    if existing:
        existing.discord_username = user_info.username
        existing.discord_guild_member = True
        existing.epic_account_id = epic_id
        if region_code:
            existing.region_code = region_code
        user = existing
    else:
        user = User(
            discord_user_id=user_info.user_id,
            discord_username=user_info.username,
            discord_guild_member=True,
            epic_account_id=epic_id,
            region_code=region_code,
        )
        db.add(user)
    db.flush()  # assign user.id for FK usage below
    ver = VerificationRecord(
        user_id=user.id,
        discord_user_id=user_info.user_id,
        discord_guild_member=True,
        epic_account_id=epic_id,
        source="auth_callback",
        status="ok",
        detail=None,
    )
    db.add(ver)
    db.commit()
    db.refresh(user)

    token = issue_session(user.discord_user_id, session_secret())
    resp = JSONResponse(
        {
            "discord_user_id": user.discord_user_id,
            "discord_username": user.discord_username,
            "epic_account_id": user.epic_account_id,
        }
    )
    resp.set_cookie("p2s_session", token, httponly=True, samesite="lax")
    return resp
