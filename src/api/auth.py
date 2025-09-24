from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.post("/auth/discord/callback")
def discord_callback(
    state: str = Query(..., description="OAuth state"),
    code: str = Query(..., description="OAuth authorization code"),
):
    # Placeholder: validate state, exchange code, check guild membership & Yunite mapping
    raise HTTPException(status_code=501, detail="Not implemented")
