import base64
import time
from collections.abc import Generator
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from sqlalchemy.orm import Session

from src.lib.auth import session_secret, verify_session
from src.lib.observability import get_logger
from src.models.models import Payout, RewardAccrual, User, VerificationRecord, WalletLink
from src.services.domain.hodl_boost_service import (
    fetch_spl_token_balance,
    get_tier_for_balance,
    tiers_as_dicts,
)

log = get_logger("api.user")

# Banano address heuristic length bounds
BANANO_ADDR_MIN_LEN = 20
BANANO_ADDR_MAX_LEN = 120

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
    request: Request,
    banano_address: str = Body(..., embed=True),
    db: Session = Depends(_get_db),  # noqa: B008 - FastAPI dependency
) -> JSONResponse:
    # rudimentary validation: must start with 'ban_'
    if not isinstance(banano_address, str) or not banano_address.startswith("ban_"):
        raise HTTPException(status_code=400, detail="Invalid Banano address")
    # Additional basic sanitation: no whitespace and reasonable length bounds
    if any(c.isspace() for c in banano_address) or not (
        BANANO_ADDR_MIN_LEN <= len(banano_address) <= BANANO_ADDR_MAX_LEN
    ):
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


_SOL_ADDR_MIN_LEN = 32
_SOL_ADDR_MAX_LEN = 64
_VERIFY_MESSAGE_MAX_AGE_SEC = 300  # 5 minutes
_VERIFY_MESSAGE_LINE_COUNT = 3


def _verify_solana_signature(address: str, message: str, signature_b64: str) -> bool:
    """Verify an ed25519 signature from a Solana wallet.

    The wallet's public key IS the address (base58-decoded to 32 bytes).
    Phantom/Solflare sign the raw UTF-8 message bytes.
    """
    try:
        # Decode base58 public key to raw 32-byte ed25519 key
        pub_bytes = _base58_decode(address)
        if len(pub_bytes) != 32:  # noqa: PLR2004
            return False
        sig_bytes = base64.b64decode(signature_b64)
        vk = VerifyKey(pub_bytes)
        vk.verify(message.encode("utf-8"), sig_bytes)
        return True
    except (BadSignatureError, Exception):
        return False


def _base58_decode(s: str) -> bytes:
    """Decode a base58 string (Bitcoin/Solana alphabet)."""
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = 0
    for ch in s:
        n = n * 58 + alphabet.index(ch)
    # Count leading 1s (= leading zero bytes)
    pad = 0
    for ch in s:
        if ch == "1":
            pad += 1
        else:
            break
    result = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\x00" * pad + result


@router.post("/me/verify-solana")
def verify_solana_wallet(
    request: Request,
    solana_address: str = Body(..., embed=True),
    signature: str = Body(..., embed=True),
    message: str = Body(..., embed=True),
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    """Link a Solana wallet and verify $JPMT token holdings for HODL boost.

    Requires a signed message proving wallet ownership:
    - message: "Verify wallet ownership for Pay2Slay\\nWallet: <addr>\\nTimestamp: <unix>"
    - signature: base64-encoded ed25519 signature from the wallet
    """
    if (
        not isinstance(solana_address, str)
        or len(solana_address) < _SOL_ADDR_MIN_LEN
        or len(solana_address) > _SOL_ADDR_MAX_LEN
    ):
        raise HTTPException(status_code=400, detail="Invalid Solana address")

    # Verify the message format and timestamp freshness
    try:
        lines = message.split("\n")
        if (
            len(lines) < _VERIFY_MESSAGE_LINE_COUNT
            or not lines[1].startswith("Wallet: ")
            or not lines[2].startswith("Timestamp: ")
        ):
            raise ValueError("Bad format")
        msg_wallet = lines[1].removeprefix("Wallet: ").strip()
        msg_ts = int(lines[2].removeprefix("Timestamp: ").strip())
        if msg_wallet != solana_address:
            raise ValueError("Address mismatch")
        if abs(time.time() - msg_ts) > _VERIFY_MESSAGE_MAX_AGE_SEC:
            raise ValueError("Expired")
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid verification message: {exc}") from exc

    # Verify ed25519 signature proves wallet ownership
    if not _verify_solana_signature(solana_address, message, signature):
        raise HTTPException(
            status_code=400, detail="Invalid wallet signature — could not verify ownership"
        )

    token = request.cookies.get("p2s_session") if request else None
    uid = verify_session(token, session_secret()) if token else None
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(User).filter(User.discord_user_id == uid).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Get HODL boost config
    app_state = getattr(getattr(request, "app", None), "state", None)
    cfg_obj = getattr(app_state, "config", None)
    payout_cfg = getattr(cfg_obj, "payout", None)

    if not payout_cfg or not payout_cfg.hodl_boost_enabled:
        raise HTTPException(status_code=400, detail="HODL boost not enabled")

    token_ca = payout_cfg.hodl_boost_token_ca
    rpc_url = payout_cfg.hodl_boost_solana_rpc

    # Fetch on-chain balance
    balance = fetch_spl_token_balance(solana_address, token_ca, rpc_url)

    # Update user record
    user.solana_wallet_address = solana_address
    user.jpmt_balance = balance
    user.jpmt_verified_at = datetime.now(UTC)
    db.commit()

    tier = get_tier_for_balance(balance)
    return JSONResponse(
        {
            "solana_address": solana_address,
            "jpmt_balance": balance,
            "tier": tier.name,
            "badge": tier.badge,
            "multiplier": tier.multiplier,
            "verified_at": user.jpmt_verified_at.isoformat(),
        }
    )


@router.get("/hodl/tiers")
def hodl_tiers() -> JSONResponse:
    """Public endpoint returning all HODL boost tiers."""
    return JSONResponse({"tiers": tiers_as_dicts()})


@router.get("/hodl/boosted")
def hodl_boosted(
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    """Public endpoint returning all users with an active HODL boost (balance > 0)."""
    users = db.query(User).filter(User.jpmt_balance > 0).order_by(User.jpmt_balance.desc()).all()
    result = []
    for u in users:
        tier = get_tier_for_balance(u.jpmt_balance or 0)
        result.append(
            {
                "discord_username": u.discord_username or "Unknown",
                "jpmt_balance": u.jpmt_balance or 0,
                "tier_name": tier.name,
                "tier_emoji": tier.emoji,
                "tier_badge": tier.badge,
                "multiplier": tier.multiplier,
                "verified_at": u.jpmt_verified_at.isoformat() if u.jpmt_verified_at else None,
            }
        )
    return JSONResponse({"boosted_users": result, "total": len(result)})


@router.post("/me/reverify")
def me_reverify(
    request: Request,
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
    from src.services.fortnite_service import FortniteService, seed_kill_baseline
    from src.services.yunite_service import YuniteService

    yunite = YuniteService(
        api_key=integrations.yunite_api_key,
        guild_id=integrations.yunite_guild_id,
        base_url=integrations.yunite_base_url,
        dry_run=integrations.dry_run,
    )
    old_epic_id = user.epic_account_id
    epic_id = yunite.get_epic_id_for_discord(user.discord_user_id)
    user.epic_account_id = epic_id
    # Seed kill baseline so only kills after linking earn payouts
    if epic_id and epic_id != old_epic_id:
        fortnite = FortniteService(
            api_key=integrations.fortnite_api_key,
            base_url=integrations.fortnite_base_url,
            per_minute_limit=int(integrations.rate_limits.get("fortnite_per_min", 60)),
            dry_run=integrations.dry_run,
        )
        user.last_settled_kill_count = seed_kill_baseline(fortnite, epic_id)
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
def me_status(request: Request, db: Session = Depends(_get_db)) -> JSONResponse:  # noqa: B008
    token = request.cookies.get("p2s_session") if request else None
    uid = verify_session(token, session_secret()) if token else None
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(User).filter(User.discord_user_id == uid).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # compute accrued rewards sum
    total_accrued = sum(Decimal(a.amount_ban) for a in user.accruals)
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
    # Get linked wallet address (most recent)
    wallet_address = None
    if user.wallet_links:
        # Get the most recently linked wallet
        latest_wallet = max(user.wallet_links, key=lambda w: w.created_at or w.id)
        wallet_address = latest_wallet.address

    # HODL boost status
    jpmt_balance = getattr(user, "jpmt_balance", 0) or 0
    tier = get_tier_for_balance(jpmt_balance)
    solana_addr = getattr(user, "solana_wallet_address", None)
    jpmt_verified = getattr(user, "jpmt_verified_at", None)

    return JSONResponse(
        {
            "discord_username": user.discord_username,
            "linked": bool(user.wallet_links),
            "wallet_address": wallet_address,
            "last_verified_at": last_verified_at,
            "last_verified_status": last_verified_status,
            "last_verified_source": last_verified_source,
            "accrued_rewards_ban": float(total_accrued),
            "solana_wallet": solana_addr,
            "jpmt_balance": jpmt_balance,
            "jpmt_tier": tier.name,
            "jpmt_badge": tier.badge,
            "jpmt_multiplier": tier.multiplier,
            "jpmt_verified_at": jpmt_verified.isoformat() if jpmt_verified else None,
        }
    )


@router.get("/me/payouts")
def me_payouts(  # noqa: PLR0913 - explicit filter params acceptable for clarity
    request: Request,
    db: Session = Depends(_get_db),  # noqa: B008
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    sort: str = "-created_at",
) -> JSONResponse:
    token = request.cookies.get("p2s_session") if request else None
    uid = verify_session(token, session_secret()) if token else None
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(User).filter(User.discord_user_id == uid).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        q = db.query(Payout).filter(Payout.user_id == user.id)
        if status:
            q = q.filter(Payout.status == status)
        # sorting
        if sort.lstrip("-") not in {"created_at", "amount_ban", "status"}:
            raise HTTPException(status_code=400, detail="invalid sort field")
        is_desc = sort.startswith("-")
        field = sort.lstrip("-")
        col = getattr(Payout, field)
        q = q.order_by(col.desc() if is_desc else col.asc())
        q = q.offset(offset).limit(min(limit, 100))
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
    except HTTPException:
        raise
    except Exception as exc:
        log.error("me_payouts_error", error=str(exc), user_id=user.id)
        raise HTTPException(status_code=500, detail=f"Failed to load payouts: {exc}") from exc


@router.get("/me/accruals")
def me_accruals(
    request: Request,
    db: Session = Depends(_get_db),  # noqa: B008
    limit: int = 50,
    offset: int = 0,
    settled: bool | None = None,
) -> JSONResponse:
    token = request.cookies.get("p2s_session") if request else None
    uid = verify_session(token, session_secret()) if token else None
    if not uid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(User).filter(User.discord_user_id == uid).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    q = db.query(RewardAccrual).filter(RewardAccrual.user_id == user.id)
    if settled is not None:
        q = q.filter(RewardAccrual.settled.is_(settled))
    q = q.order_by(RewardAccrual.created_at.desc()).offset(offset).limit(min(limit, 200))
    rows = q.all()
    return JSONResponse(
        {
            "accruals": [
                {
                    "id": a.id,
                    "kills": a.kills,
                    "amount_ban": float(a.amount_ban),
                    "settled": a.settled,
                    "epoch_minute": a.epoch_minute,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in rows
            ],
            "count": len(rows),
            "limit": limit,
            "offset": offset,
        }
    )
