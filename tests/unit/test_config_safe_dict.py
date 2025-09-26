from __future__ import annotations

from copy import deepcopy

from src.lib.config import AppConfig, IntegrationsConfig, PayoutConfig, ProductConfig


def test_safe_dict_masks_secret_like_fields() -> None:
    cfg = AppConfig(
        payout=PayoutConfig(
            payout_amount_ban_per_kill=1.0,
            scheduler_minutes=5,
            daily_payout_cap=10,
            weekly_payout_cap=50,
            reset_tz="UTC",
            settlement_order="random",
            batch_size=0,
        ),
        integrations=IntegrationsConfig(
            chain_env="testnet",
            node_rpc="http://localhost:7072",
            min_operator_balance_ban=50,
            dry_run=True,
            fortnite_base_url="https://fortnite.example/api",
            yunite_api_key="ABC123",
            yunite_guild_id="gid",
            discord_guild_id="dgid",
            discord_oauth_client_id="cid",
            discord_oauth_client_secret="supersecret",
            discord_redirect_uri="https://app/callback",
            oauth_scopes=["identify"],
            fortnite_api_key="FORT123",
            rate_limits={},
            abuse_heuristics={},
        ),
        product=ProductConfig(app_name="app", org_name="org"),
    )
    masked = cfg.safe_dict()
    # Ensure structure preserved
    assert masked["integrations"]["chain_env"] == "testnet"
    # Ensure secrets masked
    secret_fields = [
        "yunite_api_key",
        "fortnite_api_key",
        "discord_oauth_client_secret",
    ]
    for field in secret_fields:
        assert masked["integrations"][field] == "***"
    # Non-secret field not masked
    assert masked["integrations"]["discord_oauth_client_id"] == "cid"


def test_safe_dict_no_mutation() -> None:
    cfg = AppConfig(
        payout=PayoutConfig(
            payout_amount_ban_per_kill=1.0,
            scheduler_minutes=5,
            daily_payout_cap=10,
            weekly_payout_cap=50,
            reset_tz="UTC",
            settlement_order="random",
            batch_size=0,
        ),
        integrations=IntegrationsConfig(
            chain_env="testnet",
            node_rpc="http://localhost:7072",
            min_operator_balance_ban=50,
            dry_run=True,
            fortnite_base_url="https://fortnite.example/api",
            yunite_api_key="ABC123",
            yunite_guild_id="gid",
            discord_guild_id="dgid",
            discord_oauth_client_id="cid",
            discord_oauth_client_secret="supersecret",
            discord_redirect_uri="https://app/callback",
            oauth_scopes=["identify"],
            fortnite_api_key="FORT123",
            rate_limits={},
            abuse_heuristics={},
        ),
        product=ProductConfig(app_name="app", org_name="org"),
    )
    original = deepcopy(cfg.model_dump())
    _ = cfg.safe_dict()
    assert cfg.model_dump() == original
