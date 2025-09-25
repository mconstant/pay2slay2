from __future__ import annotations

import os

from prometheus_client import start_http_server
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .settlement import SchedulerConfig, run_scheduler


def main() -> None:
    # Basic config from env for local launch
    interval = int(os.getenv("P2S_INTERVAL_SECONDS", "1200"))
    min_balance = float(os.getenv("P2S_MIN_OPERATOR_BALANCE_BAN", "50"))
    dry_run = os.getenv("P2S_DRY_RUN", "true").lower() in ("1", "true", "yes")
    operator_account = os.getenv("P2S_OPERATOR_ACCOUNT", "") or None
    metrics_port = int(os.getenv("P2S_METRICS_PORT", "8001"))
    db_url = os.getenv("DATABASE_URL", "sqlite:///pay2slay.db")

    # Start Prometheus metrics server
    start_http_server(metrics_port)

    engine = create_engine(db_url)
    session_local = sessionmaker(bind=engine)

    def session_factory() -> Session:
        return session_local()

    cfg = SchedulerConfig(
        min_operator_balance_ban=min_balance,
        batch_size=None,
        daily_cap=1,
        weekly_cap=3,
        dry_run=dry_run,
        interval_seconds=interval,
        operator_account=operator_account,
    )

    run_scheduler(session_factory, cfg)


if __name__ == "__main__":  # pragma: no cover
    main()
