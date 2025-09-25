from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import JSONResponse
from typing import Generator
from sqlalchemy.orm import Session

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
    db: Session = Depends(_get_db),
) -> JSONResponse:
    if not state or not code:
        raise HTTPException(status_code=400, detail="Missing state or code")

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
    yunite = YuniteService(api_key=integ.yunite_api_key, guild_id=integ.yunite_guild_id, dry_run=integ.dry_run)

    user_info = discord.exchange_code_for_user(code)
    if not user_info.guild_member:
        raise HTTPException(status_code=403, detail="Guild membership required")
    epic_id = yunite.get_epic_id_for_discord(user_info.user_id)
    if not epic_id:
        raise HTTPException(status_code=403, detail="Yunite EpicID mapping required")

    # Upsert user
    existing = db.query(User).filter(User.discord_user_id == user_info.user_id).one_or_none()
    if existing:
        existing.discord_username = user_info.username
        existing.discord_guild_member = True
        existing.epic_account_id = epic_id
        user = existing
    else:
        user = User(
            discord_user_id=user_info.user_id,
            discord_username=user_info.username,
            discord_guild_member=True,
            epic_account_id=epic_id,
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

    return JSONResponse(
        {
            "discord_user_id": user.discord_user_id,
            "discord_username": user.discord_username,
            "epic_account_id": user.epic_account_id,
        }
    )
