from collections.abc import Generator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.models import Payout, RewardAccrual, User

router = APIRouter()


def _get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@router.get("/api/leaderboard")
def leaderboard(
    db: Session = Depends(_get_db),  # noqa: B008
    limit: int = 50,
    offset: int = 0,
) -> JSONResponse:
    """Public leaderboard showing all players, kills, and payouts. No auth required."""
    limit = min(max(limit, 1), 100)

    accrual_sub = (
        db.query(
            RewardAccrual.user_id,
            func.coalesce(func.sum(RewardAccrual.kills), 0).label("total_kills"),
            func.coalesce(func.sum(RewardAccrual.amount_ban), 0).label("total_accrued"),
        )
        .group_by(RewardAccrual.user_id)
        .subquery()
    )

    payout_sub = (
        db.query(
            Payout.user_id,
            func.coalesce(func.sum(Payout.amount_ban), 0).label("total_paid"),
        )
        .filter(Payout.status == "sent")
        .group_by(Payout.user_id)
        .subquery()
    )

    rows = (
        db.query(
            User.discord_username,
            func.coalesce(accrual_sub.c.total_kills, 0).label("total_kills"),
            func.coalesce(accrual_sub.c.total_accrued, 0).label("total_accrued"),
            func.coalesce(payout_sub.c.total_paid, 0).label("total_paid"),
        )
        .outerjoin(accrual_sub, accrual_sub.c.user_id == User.id)
        .outerjoin(payout_sub, payout_sub.c.user_id == User.id)
        .order_by(func.coalesce(accrual_sub.c.total_kills, 0).desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    total_users = db.query(func.count(User.id)).scalar() or 0

    return JSONResponse(
        {
            "players": [
                {
                    "discord_username": r.discord_username or "Unknown",
                    "total_kills": int(r.total_kills),
                    "total_accrued_ban": float(r.total_accrued),
                    "total_paid_ban": float(r.total_paid),
                }
                for r in rows
            ],
            "total": total_users,
            "limit": limit,
            "offset": offset,
        }
    )
