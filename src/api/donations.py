"""Donations API — public endpoint for donation progress and milestones."""

from __future__ import annotations

import traceback
from collections.abc import Generator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.lib.observability import get_logger
from src.services.domain.donation_service import get_donation_status

router = APIRouter()
_log = get_logger(__name__)


def _get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@router.get("/api/donations")
def donations(
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    """Public endpoint returning donation progress, milestones, and current multiplier."""
    try:
        return JSONResponse(get_donation_status(db))
    except Exception:
        _log.exception("donations_endpoint_error")
        tb = traceback.format_exc()
        return JSONResponse(
            {"error": "donations_error", "detail": tb},
            status_code=500,
        )
