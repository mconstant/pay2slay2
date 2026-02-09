"""Demo-only endpoints: login simulation, data seeding, scheduler trigger.

All endpoints in this module require dry_run=true and return 403 otherwise.
"""

from __future__ import annotations

import hashlib
import random
import time
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.lib.auth import issue_session, session_secret
from src.models.models import (
    AdminUser,
    Payout,
    RewardAccrual,
    User,
    VerificationRecord,
    WalletLink,
)

router = APIRouter()

_DEMO_USERS = [
    ("demo_user_001", "DemoPlayer", "epic_demo_001"),
    ("demo_user_002", "FragMaster99", "epic_demo_002"),
    ("demo_user_003", "BananoHunter", "epic_demo_003"),
]


def _get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def _require_dry_run(request: Request) -> None:
    config = getattr(getattr(request, "app", None), "state", None)
    cfg = getattr(config, "config", None)
    integ = getattr(cfg, "integrations", None)
    if not integ or not integ.dry_run:
        raise HTTPException(status_code=403, detail="Only available in dry_run mode")


def _upsert_demo_users(db: Session) -> tuple[list[User], int]:
    """Create or fetch demo users, returning (users, created_count)."""
    users: list[User] = []
    created = 0
    for did, name, eid in _DEMO_USERS:
        existing = db.query(User).filter(User.discord_user_id == did).one_or_none()
        if existing:
            users.append(existing)
        else:
            u = User(
                discord_user_id=did,
                discord_username=name,
                discord_guild_member=True,
                epic_account_id=eid,
            )
            db.add(u)
            db.flush()
            users.append(u)
            created += 1
    # Add wallet links for users without one
    for u in users:
        if not db.query(WalletLink).filter(WalletLink.user_id == u.id).one_or_none():
            wl = WalletLink(
                user_id=u.id,
                address=f"ban_1demo{u.discord_user_id[-3:]}{'x' * 50}"[:64],
                is_primary=True,
                verified=True,
            )
            db.add(wl)
    return users, created


def _seed_accruals(db: Session, users: list[User]) -> int:
    """Create random unsettled accruals over the past few hours."""
    epoch_base = int(time.time()) // 60
    created = 0
    for u in users:
        for i in range(random.randint(3, 8)):
            epoch_min = epoch_base - (i * 20) - random.randint(0, 10)
            existing = (
                db.query(RewardAccrual)
                .filter(RewardAccrual.user_id == u.id, RewardAccrual.epoch_minute == epoch_min)
                .one_or_none()
            )
            if existing:
                continue
            kills = random.randint(1, 7)
            acc = RewardAccrual(
                user_id=u.id,
                kills=kills,
                amount_ban=Decimal(str(kills * 2.1)),
                epoch_minute=epoch_min,
                settled=False,
            )
            db.add(acc)
            created += 1
    return created


def _seed_payouts(db: Session, user: User) -> tuple[int, int]:
    """Create settled accruals + payouts for a single user."""
    now = datetime.now(UTC)
    epoch_base = int(time.time()) // 60
    wl = db.query(WalletLink).filter(WalletLink.user_id == user.id).first()
    addr = wl.address if wl else "ban_1demo001"
    accrual_count = 0
    payout_count = 0
    for i in range(2):
        p_epoch = epoch_base - 1000 - (i * 200)
        existing = (
            db.query(RewardAccrual)
            .filter(RewardAccrual.user_id == user.id, RewardAccrual.epoch_minute == p_epoch)
            .one_or_none()
        )
        if existing:
            continue
        kills = random.randint(5, 15)
        amount = Decimal(str(kills * 2.1))
        payout = Payout(
            user_id=user.id,
            address=addr,
            amount_ban=amount,
            tx_hash=hashlib.sha256(f"demo_tx_{i}_{time.time()}".encode()).hexdigest()[:64],
            status="sent",
            idempotency_key=f"demo_idem_{i}_{int(time.time())}",
        )
        db.add(payout)
        db.flush()
        acc = RewardAccrual(
            user_id=user.id,
            kills=kills,
            amount_ban=amount,
            epoch_minute=p_epoch,
            settled=True,
            settled_at=now - timedelta(hours=i + 1),
            payout_id=payout.id,
        )
        db.add(acc)
        accrual_count += 1
        payout_count += 1
    return accrual_count, payout_count


@router.post("/auth/demo-login")
def demo_login(
    request: Request,
    _: None = Depends(_require_dry_run),
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    """Simulate Discord OAuth login in dry-run mode."""
    discord_user_id = "demo_user_001"
    username = "DemoPlayer"
    epic_id = "epic_demo_001"

    existing = db.query(User).filter(User.discord_user_id == discord_user_id).one_or_none()
    if existing:
        user = existing
        user.discord_username = username
        user.epic_account_id = epic_id
    else:
        user = User(
            discord_user_id=discord_user_id,
            discord_username=username,
            discord_guild_member=True,
            epic_account_id=epic_id,
        )
        db.add(user)
    db.flush()

    ver = VerificationRecord(
        user_id=user.id,
        discord_user_id=discord_user_id,
        discord_guild_member=True,
        epic_account_id=epic_id,
        source="demo_login",
        status="ok",
        detail=None,
    )
    db.add(ver)
    db.commit()
    db.refresh(user)

    token = issue_session(discord_user_id, session_secret())
    resp = JSONResponse(
        {
            "discord_user_id": user.discord_user_id,
            "discord_username": user.discord_username,
            "epic_account_id": user.epic_account_id,
        }
    )
    resp.set_cookie("p2s_session", token, httponly=True, samesite="lax")
    return resp


@router.post("/demo/seed")
def demo_seed(
    request: Request,
    _: None = Depends(_require_dry_run),
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    """Seed the database with realistic demo data for demonstrations."""
    users, created_users = _upsert_demo_users(db)
    created_accruals = _seed_accruals(db, users)
    extra_accruals, created_payouts = _seed_payouts(db, users[0])
    created_accruals += extra_accruals

    # Ensure admin user exists
    if not db.query(AdminUser).filter(AdminUser.email == "admin@example.org").one_or_none():
        db.add(AdminUser(email="admin@example.org", is_active=True))

    db.commit()
    return JSONResponse(
        {
            "summary": f"{created_users} users, {created_accruals} accruals, {created_payouts} payouts",
            "users": created_users,
            "accruals": created_accruals,
            "payouts": created_payouts,
        }
    )


@router.post("/demo/run-scheduler")
def demo_run_scheduler(
    request: Request,
    _: None = Depends(_require_dry_run),
    db: Session = Depends(_get_db),  # noqa: B008
) -> JSONResponse:
    """Run one accrual+settlement cycle inline (dry-run only)."""
    now = datetime.now(UTC)
    epoch_min = int(time.time()) // 60
    config = request.app.state.config
    ban_per_kill = Decimal(str(config.payout.payout_amount_ban_per_kill))

    demo_ids = [d[0] for d in _DEMO_USERS]
    users = db.query(User).filter(User.discord_user_id.in_(demo_ids)).all()
    accrued = 0
    for u in users:
        kills = random.randint(1, 5)
        existing = (
            db.query(RewardAccrual)
            .filter(RewardAccrual.user_id == u.id, RewardAccrual.epoch_minute == epoch_min)
            .one_or_none()
        )
        if existing:
            continue
        acc = RewardAccrual(
            user_id=u.id,
            kills=kills,
            amount_ban=Decimal(str(kills)) * ban_per_kill,
            epoch_minute=epoch_min,
            settled=False,
        )
        db.add(acc)
        accrued += 1

    settled = _settle_users(db, users, now, epoch_min)
    db.commit()
    return JSONResponse(
        {
            "summary": f"Accrued {accrued} records, settled {settled} payouts",
            "accrued": accrued,
            "settled": settled,
        }
    )


def _settle_users(db: Session, users: list[User], now: datetime, epoch_min: int) -> int:
    """Settle unsettled accruals into payouts for users with wallets."""
    settled = 0
    for u in users:
        wl = db.query(WalletLink).filter(WalletLink.user_id == u.id).first()
        if not wl:
            continue
        unsettled = (
            db.query(RewardAccrual)
            .filter(RewardAccrual.user_id == u.id, RewardAccrual.settled.is_(False))
            .all()
        )
        if not unsettled:
            continue
        total = sum(a.amount_ban for a in unsettled)
        idem_ids = sorted(str(a.id) for a in unsettled)
        idem_key = hashlib.sha256(",".join(idem_ids).encode()).hexdigest()
        if db.query(Payout).filter(Payout.idempotency_key == idem_key).one_or_none():
            continue
        payout = Payout(
            user_id=u.id,
            address=wl.address,
            amount_ban=total,
            tx_hash=hashlib.sha256(f"dry_{u.id}_{epoch_min}_{time.time()}".encode()).hexdigest()[
                :64
            ],
            status="sent",
            idempotency_key=idem_key,
        )
        db.add(payout)
        db.flush()
        for a in unsettled:
            a.settled = True
            a.settled_at = now
            a.payout_id = payout.id
        settled += 1
    return settled
