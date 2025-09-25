from __future__ import annotations

import os
from collections.abc import Mapping, MutableMapping
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


def _expand_env(obj: Any) -> Any:
    """Recursively expand environment variables in strings within a structure."""
    if isinstance(obj, str):
        return os.path.expandvars(obj)
    if isinstance(obj, list):
        return [_expand_env(i) for i in obj]
    if isinstance(obj, tuple):
        return tuple(_expand_env(i) for i in obj)
    if isinstance(obj, Mapping):
        return {k: _expand_env(v) for k, v in obj.items()}
    return obj


class PayoutConfig(BaseModel):
    payout_amount_ban_per_kill: float = Field(..., ge=0)
    scheduler_minutes: int = Field(..., ge=1)
    daily_payout_cap: int = Field(..., ge=0)
    weekly_payout_cap: int = Field(..., ge=0)
    reset_tz: str = Field(..., description="Timezone name for cap resets, e.g., UTC")
    settlement_order: str = Field("random")
    batch_size: int = Field(0, ge=0, description="0 means unlimited")


class IntegrationsConfig(BaseModel):
    chain_env: str = Field(..., description="testnet or mainnet")
    node_rpc: str = Field("", description="Banano node RPC endpoint")
    min_operator_balance_ban: float = Field(50, ge=0)
    dry_run: bool = True
    fortnite_base_url: str = Field(
        "https://fortnite.example.api/v1", description="Fortnite stats API base URL"
    )
    yunite_api_key: str = Field(...)
    yunite_guild_id: str = Field(...)
    discord_guild_id: str = Field(...)
    discord_oauth_client_id: str = Field(...)
    discord_oauth_client_secret: str = Field(...)
    discord_redirect_uri: str = Field(...)
    oauth_scopes: list[str] = Field(default_factory=lambda: ["identify", "guilds"])
    fortnite_api_key: str = Field(...)
    rate_limits: dict[str, Any] = Field(default_factory=dict)
    abuse_heuristics: dict[str, Any] = Field(default_factory=dict)


class ProductConfig(BaseModel):
    app_name: str
    org_name: str
    banner_url: str = ""
    media_kit_url: str = ""
    default_locale: str = "en"
    feature_flags: dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseModel):
    payout: PayoutConfig
    integrations: IntegrationsConfig
    product: ProductConfig


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required config file: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, MutableMapping):
        raise ValueError(f"Config must be a mapping at top level: {path}")
    expanded = _expand_env(dict(data))
    assert isinstance(expanded, dict)
    return expanded


def _default_configs_dir() -> Path:
    # Allow override via CONFIG_DIR; fallback to repo-root/configs
    env_dir = os.getenv("CONFIG_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return (Path.cwd() / "configs").resolve()


def load_config(configs_dir: Path | None = None) -> AppConfig:
    """Load and validate configuration from three YAML files in configs_dir.

    Files required:
      - payout.yaml
      - integrations.yaml
      - product.yaml
    """
    base = configs_dir or _default_configs_dir()
    payout = _read_yaml(base / "payout.yaml")
    integrations = _read_yaml(base / "integrations.yaml")
    product = _read_yaml(base / "product.yaml")

    return AppConfig(
        payout=PayoutConfig(**payout),
        integrations=IntegrationsConfig(**integrations),
        product=ProductConfig(**product),
    )


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Cached accessor for the application configuration."""
    return load_config()


__all__ = [
    "AppConfig",
    "IntegrationsConfig",
    "PayoutConfig",
    "ProductConfig",
    "get_config",
    "load_config",
]
