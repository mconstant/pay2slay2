from __future__ import annotations

import os

from prometheus_client import Counter, start_http_server
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.lib.config import get_config
from src.lib.observability import get_logger, get_tracer
from src.services.fortnite_service import FortniteService

from .accrual import AccrualJobConfig, run_accrual
from .settlement import SchedulerConfig, run_settlement

log = get_logger("jobs.main")
JOB_ERRORS = Counter("scheduler_errors_total", "Unhandled errors in main scheduler loop")


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

    cfg_obj = get_config()
    integrations = cfg_obj.integrations
    fortnite = FortniteService(
        api_key=integrations.fortnite_api_key,
        base_url=getattr(integrations, "fortnite_base_url", "https://fortnite.example.api/v1"),
        per_minute_limit=int(integrations.rate_limits.get("fortnite_per_minute", 60)),
        dry_run=integrations.dry_run,
    )
    accrual_cfg = AccrualJobConfig(batch_size=None, dry_run=integrations.dry_run)

    import time

    tracer = get_tracer("scheduler")
    while True:  # pragma: no cover
        session: Session = session_factory()
        try:
            try:
                with tracer.start_as_current_span(
                    "accrual_cycle",
                    attributes={
                        "scheduler.interval_sec": interval,
                        "scheduler.dry_run": dry_run,
                        "fortnite.base_url": fortnite.base_url,
                    },
                ):
                    accrual_res = run_accrual(session, fortnite, accrual_cfg)
                    log.info("accrual_cycle", **accrual_res)
            except Exception as exc:  # pragma: no cover
                JOB_ERRORS.inc()
                log.error("accrual_cycle_error", error=str(exc))
            try:
                from src.services.banano_client import BananoClient

                banano = BananoClient(node_url=integrations.node_rpc, dry_run=integrations.dry_run)
                if banano.has_min_balance(cfg.min_operator_balance_ban, operator_account):
                    with tracer.start_as_current_span(
                        "settlement_cycle",
                        attributes={
                            "scheduler.interval_sec": interval,
                            "scheduler.dry_run": dry_run,
                            "banano.min_balance": cfg.min_operator_balance_ban,
                        },
                    ):
                        run_settlement(session, cfg)
                else:
                    log.warning("settlement_skipped_low_balance")
            except Exception as exc:  # pragma: no cover
                JOB_ERRORS.inc()
                log.error("settlement_cycle_error", error=str(exc))
        finally:
            session.close()
        time.sleep(interval)


if __name__ == "__main__":  # pragma: no cover
    main()
