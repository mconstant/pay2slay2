"""Promotional event system with feature-flag gating.

Each promo is defined as a dataclass with date range, multiplier, cap overrides,
and display metadata.  ``get_active_promo()`` returns the first matching promo
(or *None*) based on the current UTC date **and** its feature flag being truthy.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any


@dataclass(frozen=True)
class Promo:
    """An active promotional event."""

    key: str  # unique machine key (e.g. "lunar_new_year_2026")
    name: str  # display name
    emoji: str  # primary emoji for badges/banners
    tagline: str  # short one-liner
    multiplier: float  # applied on top of all other multipliers
    daily_cap: int | None  # override daily kill cap (None = keep default)
    weekly_cap: int | None  # override weekly kill cap (None = keep default)
    start: date  # inclusive
    end: date  # inclusive
    theme: dict[str, str]  # CSS custom properties to inject (e.g. accent colours)
    feature_flag_env: str  # env var that must be truthy to activate


# ── Promo Registry ──────────────────────────────────────
# Add future promos here.  The first matching active promo wins.

_PROMOS: list[Promo] = [
    Promo(
        key="lunar_new_year_2026",
        name="Lunar New Year — Year of the Fire Horse 🐴🔥",
        emoji="🧧",
        tagline="Gong xi fa cai! 1.88x rewards for the Year of the Fire Horse!",
        multiplier=1.88,
        daily_cap=200,
        weekly_cap=1000,
        start=date(2026, 2, 17),
        end=date(2026, 2, 25),
        theme={
            "--promo-primary": "#D4171E",  # lucky red
            "--promo-secondary": "#FFD700",  # gold
            "--promo-glow": "rgba(212,23,30,.15)",
            "--promo-gradient": "linear-gradient(135deg, #D4171E 0%, #FFD700 100%)",
        },
        feature_flag_env="P2S_LUNAR_NEW_YEAR",
    ),
]


def _flag_enabled(env_var: str) -> bool:
    """Return True if the env var is set to a truthy value."""
    val = os.getenv(env_var, "").strip().lower()
    return val not in ("", "0", "false", "no", "off")


def get_active_promo(now: datetime | None = None) -> Promo | None:
    """Return the first promo whose date range and feature flag both match, or None."""
    today = (now or datetime.now(UTC)).date()
    for p in _PROMOS:
        if p.start <= today <= p.end and _flag_enabled(p.feature_flag_env):
            return p
    return None


def promo_to_dict(p: Promo) -> dict[str, Any]:
    """Serialise a Promo for the JSON config API."""
    return {
        "key": p.key,
        "name": p.name,
        "emoji": p.emoji,
        "tagline": p.tagline,
        "multiplier": p.multiplier,
        "daily_cap": p.daily_cap,
        "weekly_cap": p.weekly_cap,
        "start": p.start.isoformat(),
        "end": p.end.isoformat(),
        "theme": p.theme,
        "days_remaining": max(0, (p.end - date.today()).days + 1),
    }


__all__ = ["Promo", "get_active_promo", "promo_to_dict"]
