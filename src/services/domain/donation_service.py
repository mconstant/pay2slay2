"""Donation milestones and tracking service.

Defines the milestone tiers from 0 → 1,000,000 BAN with fun names and payout boosts.
Provides helpers for recording donations and querying current milestone status.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.models import DonationLedger


@dataclass(frozen=True)
class Milestone:
    """A donation milestone tier."""

    threshold: int  # BAN donated to unlock
    name: str  # fun event name
    emoji: str
    description: str
    payout_multiplier: float  # applied to ban_per_kill during accrual


# Ordered by threshold ascending
MILESTONES: list[Milestone] = [
    Milestone(
        threshold=0,
        name="Fresh Spawn",
        emoji="🌱",
        description="The journey begins. Standard payouts.",
        payout_multiplier=1.0,
    ),
    Milestone(
        threshold=1_000,
        name="First Blood",
        emoji="🩸",
        description="1K donated! Payouts boosted 10%.",
        payout_multiplier=1.1,
    ),
    Milestone(
        threshold=5_000,
        name="Loot Drop",
        emoji="📦",
        description="5K donated! Payouts boosted 15%.",
        payout_multiplier=1.15,
    ),
    Milestone(
        threshold=10_000,
        name="Supply Drop",
        emoji="🪂",
        description="10K donated! Payouts boosted 20%.",
        payout_multiplier=1.2,
    ),
    Milestone(
        threshold=25_000,
        name="Storm Surge",
        emoji="⛈️",
        description="25K donated! Payouts boosted 30%.",
        payout_multiplier=1.3,
    ),
    Milestone(
        threshold=50_000,
        name="Airdrop Inbound",
        emoji="🛩️",
        description="50K donated! Payouts boosted 40%.",
        payout_multiplier=1.4,
    ),
    Milestone(
        threshold=100_000,
        name="Victory Royale",
        emoji="👑",
        description="100K donated! Payouts boosted 50%.",
        payout_multiplier=1.5,
    ),
    Milestone(
        threshold=250_000,
        name="Mythic Rarity",
        emoji="💎",
        description="250K donated! Payouts DOUBLED.",
        payout_multiplier=2.0,
    ),
    Milestone(
        threshold=500_000,
        name="The Monke Awakens",
        emoji="🐒",
        description="500K donated! Payouts boosted 2.5x!",
        payout_multiplier=2.5,
    ),
    Milestone(
        threshold=1_000_000,
        name="Potassium Singularity",
        emoji="🍌",
        description="1 MILLION BAN! Payouts TRIPLED. GG.",
        payout_multiplier=3.0,
    ),
]

GOAL_BAN = 1_000_000


def get_total_donated(session: Session) -> Decimal:
    """Return the cumulative sum of all donation ledger entries."""
    total = session.query(func.coalesce(func.sum(DonationLedger.amount_ban), 0)).scalar()
    return Decimal(str(total))


def get_current_milestone(total_donated: Decimal) -> Milestone:
    """Return the highest-unlocked milestone for the given donation total."""
    current = MILESTONES[0]
    for m in MILESTONES:
        if total_donated >= m.threshold:
            current = m
        else:
            break
    return current


def get_next_milestone(total_donated: Decimal) -> Milestone | None:
    """Return the next milestone to unlock, or None if all are unlocked."""
    for m in MILESTONES:
        if total_donated < m.threshold:
            return m
    return None


def record_donation(  # noqa: PLR0913
    session: Session,
    amount_ban: Decimal,
    blocks_received: int = 0,
    source: str = "receive",
    note: str | None = None,
    sender_address: str | None = None,
) -> DonationLedger | None:
    """Record a donation entry if amount > 0. Returns the ledger row or None."""
    if amount_ban <= 0:
        return None
    entry = DonationLedger(
        amount_ban=amount_ban,
        blocks_received=blocks_received,
        source=source,
        note=note,
        sender_address=sender_address,
    )
    session.add(entry)
    session.flush()
    return entry


def get_donation_leaderboard(session: Session, limit: int = 50) -> list[dict[str, object]]:
    """Return top donors grouped by sender_address, ordered by total donated."""
    rows = (
        session.query(
            DonationLedger.sender_address,
            func.sum(DonationLedger.amount_ban).label("total"),
            func.count(DonationLedger.id).label("donations"),
        )
        .filter(DonationLedger.sender_address.isnot(None))
        .filter(DonationLedger.sender_address != "")
        .group_by(DonationLedger.sender_address)
        .order_by(func.sum(DonationLedger.amount_ban).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "address": row.sender_address,
            "total_donated": round(float(row.total), 2),
            "donation_count": row.donations,
        }
        for row in rows
    ]


def get_donation_status(session: Session) -> dict[str, object]:
    """Build the full donation status dict for the API."""
    total = get_total_donated(session)
    current = get_current_milestone(total)
    nxt = get_next_milestone(total)
    total_f = float(total)

    milestones_list = []
    for m in MILESTONES:
        milestones_list.append(
            {
                "threshold": m.threshold,
                "name": m.name,
                "emoji": m.emoji,
                "description": m.description,
                "payout_multiplier": m.payout_multiplier,
                "unlocked": total_f >= m.threshold,
            }
        )

    return {
        "total_donated": round(total_f, 2),
        "goal": GOAL_BAN,
        "progress_pct": min(round(total_f / GOAL_BAN * 100, 2), 100),
        "current_milestone": {
            "name": current.name,
            "emoji": current.emoji,
            "description": current.description,
            "payout_multiplier": current.payout_multiplier,
            "threshold": current.threshold,
        },
        "next_milestone": (
            {
                "name": nxt.name,
                "emoji": nxt.emoji,
                "description": nxt.description,
                "threshold": nxt.threshold,
                "remaining": round(nxt.threshold - total_f, 2),
            }
            if nxt
            else None
        ),
        "milestones": milestones_list,
        "leaderboard": get_donation_leaderboard(session),
    }
