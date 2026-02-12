from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from src.lib.config import get_config
from src.services.yunite_service import YuniteService

router = APIRouter()


@router.get("/config/product")
def get_product_config() -> JSONResponse:
    cfg = get_config()
    product = cfg.product
    integrations = cfg.integrations
    # Override dry_run_banner based on actual dry_run setting
    feature_flags = dict(product.feature_flags)
    feature_flags["dry_run_banner"] = integrations.dry_run
    return JSONResponse(
        {
            "app_name": product.app_name,
            "org_name": product.org_name,
            "banner_url": product.banner_url,
            "media_kit_url": product.media_kit_url,
            "default_locale": product.default_locale,
            "discord_invite_url": product.discord_invite_url,
            "feature_flags": feature_flags,
        }
    )


@router.get("/config/payout")
def get_payout_config() -> JSONResponse:
    """Return payout configuration including scheduler timing.
    
    This endpoint is intentionally public (no authentication required) as it only
    exposes non-sensitive timing and reward configuration that is useful for
    displaying UI elements like countdown timers.
    """
    cfg = get_config()
    payout = cfg.payout
    return JSONResponse(
        {
            "payout_amount_ban_per_kill": payout.payout_amount_ban_per_kill,
            "scheduler_minutes": payout.scheduler_minutes,
            "daily_payout_cap": payout.daily_payout_cap,
            "weekly_payout_cap": payout.weekly_payout_cap,
            "reset_tz": payout.reset_tz,
            "settlement_order": payout.settlement_order,
            "batch_size": payout.batch_size,
        }
    )


@router.get("/debug/yunite")
def debug_yunite(
    discord_user_id: str = Query(..., description="Discord user ID to lookup"),
) -> JSONResponse:
    """Debug endpoint to test Yunite API responses. Only available in demo mode."""
    cfg = get_config()
    integ = cfg.integrations
    yunite = YuniteService(
        api_key=integ.yunite_api_key,
        guild_id=integ.yunite_guild_id,
        base_url=integ.yunite_base_url,
        dry_run=integ.dry_run,
    )
    result = yunite.get_member_debug(discord_user_id)
    result["config"] = {
        "guild_id": integ.yunite_guild_id,
        "base_url": integ.yunite_base_url,
        "dry_run": integ.dry_run,
    }
    return JSONResponse(result)
