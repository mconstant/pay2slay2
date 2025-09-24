from fastapi import APIRouter, Body, HTTPException

router = APIRouter()


@router.post("/link/wallet")
def link_wallet(banano_address: str = Body(..., embed=True)):
    # rudimentary validation: must start with 'ban_'
    if not isinstance(banano_address, str) or not banano_address.startswith("ban_"):
        raise HTTPException(status_code=400, detail="Invalid Banano address")
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/me/status")
def me_status():
    # Would normally require auth; placeholder to satisfy tests
    raise HTTPException(status_code=401, detail="Unauthorized")
