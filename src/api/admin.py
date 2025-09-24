from fastapi import APIRouter, Body, HTTPException

router = APIRouter(prefix="/admin")


@router.post("/reverify")
def admin_reverify(discord_id: str = Body(..., embed=True)):
    # Placeholder: require admin auth; not implemented
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/payouts/retry")
def admin_payouts_retry(payout_id: str = Body(..., embed=True)):
    # Placeholder: require admin auth; not implemented
    raise HTTPException(status_code=501, detail="Not implemented")
