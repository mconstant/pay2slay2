from __future__ import annotations

import os
import re
from collections.abc import Mapping, MutableMapping
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

_ENV_DEFAULT_RE = re.compile(r"\$\{([^}]+?):-([^}]*)\}")


def _expand_env(obj: Any) -> Any:
    """Recursively expand environment variables in strings within a structure.

    Supports ``${VAR:-default}`` syntax (Python's os.path.expandvars does not).
    Unexpanded ``${VAR}`` references (env var not set) are replaced with empty
    string so Pydantic defaults can kick in.
    """
    if isinstance(obj, str):
        # First, handle ${VAR:-default} patterns that os.path.expandvars can't
        def _replace_with_default(m: re.Match[str]) -> str:
            var_name, default_val = m.group(1), m.group(2)
            return os.environ.get(var_name, default_val)

        expanded = _ENV_DEFAULT_RE.sub(_replace_with_default, obj)
        # Then expand remaining $VAR / ${VAR} references
        expanded = os.path.expandvars(expanded)
        # If expandvars left a ${...} reference, the var was unset — use empty string
        if expanded.startswith("${") and expanded.endswith("}"):
            return ""
        return expanded
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
    seed_fund_ban: float = Field(
        0, ge=0, description="Initial operator fund (BAN) for sustainability calc"
    )
    # Solana memecoin HODL boost
    hodl_boost_enabled: bool = Field(False, description="Enable token HODL payout multiplier")
    hodl_boost_token_ca: str = Field("", description="SPL token contract address for HODL boost")
    hodl_boost_solana_rpc: str = Field(
        "https://api.mainnet-beta.solana.com", description="Solana RPC endpoint"
    )


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
    yunite_base_url: str = Field("https://yunite.xyz/api", description="Yunite API base URL")
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
    discord_invite_url: str = Field("", description="Public Discord server invite URL")
    feature_flags: dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseModel):
    payout: PayoutConfig
    integrations: IntegrationsConfig
    product: ProductConfig

    def safe_dict(self) -> dict[str, Any]:  # pragma: no cover - formatting utility
        """Return a dictionary representation with secrets masked for safe logging.

        Only exposes the shape; any field name containing common secret substrings is redacted.
        """
        raw = self.model_dump()
        secret_keys = {"key", "secret", "token", "password"}

        def _mask(obj: Any) -> Any:
            if isinstance(obj, dict):
                masked: dict[str, Any] = {}
                for k, v in obj.items():
                    if any(s in k.lower() for s in secret_keys):
                        masked[k] = "***"
                    else:
                        masked[k] = _mask(v)
                return masked
            if isinstance(obj, list):
                return [_mask(i) for i in obj]
            return obj

        masked_root = _mask(raw)
        # Guarantee return type as dict[str, Any]
        if isinstance(masked_root, dict):
            return masked_root
        raise TypeError("safe_dict produced non-dict root")


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

    # Allow P2S_DRY_RUN env var to override YAML (booleans can't expand via ${} cleanly)
    dry_run_env = os.getenv("P2S_DRY_RUN")
    if dry_run_env is not None:
        integrations["dry_run"] = dry_run_env.lower() not in ("false", "0", "no", "off")

    # Allow cap overrides via env vars (persist across deploys)
    daily_cap_env = os.getenv("P2S_DAILY_CAP")
    if daily_cap_env is not None:
        payout["daily_payout_cap"] = int(daily_cap_env)
    weekly_cap_env = os.getenv("P2S_WEEKLY_CAP")
    if weekly_cap_env is not None:
        payout["weekly_payout_cap"] = int(weekly_cap_env)

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
