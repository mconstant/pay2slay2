from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.lib.config import get_config

router = APIRouter()


@router.get("/config/product")
def get_product_config() -> JSONResponse:
    cfg = get_config().product
    return JSONResponse(
        {
            "app_name": cfg.app_name,
            "org_name": cfg.org_name,
            "banner_url": cfg.banner_url,
            "media_kit_url": cfg.media_kit_url,
            "default_locale": cfg.default_locale,
            "feature_flags": cfg.feature_flags,
        }
    )
