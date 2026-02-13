"""HODL boost service for Solana SPL token holders.

Defines HODL tiers with payout multipliers and provides helpers
to query on-chain token balances and compute boost levels.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from src.lib.observability import get_logger

log = get_logger("hodl_boost")


@dataclass(frozen=True)
class HodlTier:
    """A HODL boost tier."""

    threshold: int  # minimum token balance to qualify
    name: str
    emoji: str
    badge: str  # short badge label
    description: str
    multiplier: float  # payout multiplier (1.0 = no boost)


# Ordered ascending by threshold.
# $JPMT assumed ~1B max supply.  Tiers incentivize meaningful holding.
HODL_TIERS: list[HodlTier] = [
    HodlTier(
        threshold=0,
        name="No Bag",
        emoji="🐣",
        badge="",
        description="No $JPMT detected. Standard payouts.",
        multiplier=1.0,
    ),
    HodlTier(
        threshold=10_000,
        name="Bronze HODLr",
        emoji="🥉",
        badge="🥉",
        description="10K $JPMT — 10% payout boost!",
        multiplier=1.10,
    ),
    HodlTier(
        threshold=100_000,
        name="Silver HODLr",
        emoji="🥈",
        badge="🥈",
        description="100K $JPMT — 20% payout boost!",
        multiplier=1.20,
    ),
    HodlTier(
        threshold=1_000_000,
        name="Gold HODLr",
        emoji="🥇",
        badge="🥇",
        description="1M $JPMT — 35% payout boost!",
        multiplier=1.35,
    ),
    HodlTier(
        threshold=10_000_000,
        name="Diamond HODLr",
        emoji="💎",
        badge="💎",
        description="10M $JPMT — 50% payout boost!",
        multiplier=1.50,
    ),
    HodlTier(
        threshold=100_000_000,
        name="Whale HODLr",
        emoji="🐋",
        badge="🐋",
        description="100M $JPMT — 75% payout boost!",
        multiplier=1.75,
    ),
]


def get_tier_for_balance(balance: int) -> HodlTier:
    """Return the highest tier the given balance qualifies for."""
    tier = HODL_TIERS[0]
    for t in HODL_TIERS:
        if balance >= t.threshold:
            tier = t
    return tier


def get_multiplier_for_balance(balance: int) -> float:
    """Return the payout multiplier for a given token balance."""
    return get_tier_for_balance(balance).multiplier


def tiers_as_dicts() -> list[dict[str, object]]:
    """Return all tiers as JSON-serializable dicts (for API/frontend)."""
    return [
        {
            "threshold": t.threshold,
            "name": t.name,
            "emoji": t.emoji,
            "badge": t.badge,
            "description": t.description,
            "multiplier": t.multiplier,
        }
        for t in HODL_TIERS
    ]


def fetch_spl_token_balance(
    wallet_address: str,
    token_mint: str,
    rpc_url: str = "https://api.mainnet-beta.solana.com",
    timeout: float = 10.0,
) -> int:
    """Query Solana RPC for the SPL token balance of a wallet.

    Returns the integer token amount (UI amount, accounting for decimals).
    Returns 0 on any error (network, bad address, no token account, etc.).
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            wallet_address,
            {"mint": token_mint},
            {"encoding": "jsonParsed"},
        ],
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(rpc_url, json=payload)
            data = resp.json()
        accounts = data.get("result", {}).get("value", [])
        total = 0
        for acct in accounts:
            info = acct.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
            token_amount = info.get("tokenAmount", {})
            # uiAmount is the human-readable value (already divided by decimals)
            ui_amount = token_amount.get("uiAmount")
            if ui_amount is not None:
                total += int(ui_amount)
        log.info(
            "spl_balance_fetched",
            wallet=wallet_address[:8] + "...",
            mint=token_mint[:8] + "...",
            balance=total,
        )
        return total
    except Exception as exc:
        log.warning(
            "spl_balance_fetch_failed",
            wallet=wallet_address[:8] + "...",
            error=str(exc),
        )
        return 0
