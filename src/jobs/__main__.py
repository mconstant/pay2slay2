from __future__ import annotations

import os
import random
import time

from dotenv import load_dotenv
from prometheus_client import Counter, start_http_server

load_dotenv()
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from src.lib.config import get_config  # noqa: E402
from src.lib.observability import get_logger, get_tracer  # noqa: E402
from src.services.fortnite_service import FortniteService  # noqa: E402

from .accrual import AccrualJobConfig, run_accrual  # noqa: E402
from .settlement import SchedulerConfig, run_settlement  # noqa: E402

log = get_logger("jobs.main")
JOB_ERRORS = Counter("scheduler_errors_total", "Unhandled errors in main scheduler loop")


def _build_scheduler_components() -> tuple[SchedulerConfig, FortniteService, AccrualJobConfig]:
    interval = int(os.getenv("P2S_INTERVAL_SECONDS", "1200"))
    min_balance = float(os.getenv("P2S_MIN_OPERATOR_BALANCE_BAN", "50"))
    dry_run = os.getenv("P2S_DRY_RUN", "true").lower() in ("1", "true", "yes")
    operator_account = os.getenv("P2S_OPERATOR_ACCOUNT", "") or None
    cfg_obj = get_config()
    integrations = cfg_obj.integrations
    cfg = SchedulerConfig(
        min_operator_balance_ban=min_balance,
        batch_size=None,
        daily_cap=1,
        weekly_cap=3,
        dry_run=dry_run,
        interval_seconds=interval,
        operator_account=operator_account,
        node_url=integrations.node_rpc,
    )
    fortnite = FortniteService(
        api_key=integrations.fortnite_api_key,
        base_url=getattr(integrations, "fortnite_base_url", "https://fortnite.example.api/v1"),
        per_minute_limit=int(integrations.rate_limits.get("fortnite_per_minute", 60)),
        dry_run=integrations.dry_run,
    )
    accrual_cfg = AccrualJobConfig(batch_size=None, dry_run=integrations.dry_run)
    return cfg, fortnite, accrual_cfg


def _run_once(
    session: Session,
    scheduler_cfg: SchedulerConfig,
    fortnite: FortniteService,
    accrual_cfg: AccrualJobConfig,
    tracer_name: str = "scheduler",
) -> None:
    tracer = get_tracer(tracer_name)
    cfg = scheduler_cfg
    try:
        with tracer.start_as_current_span(
            "accrual_cycle",
            attributes={
                "scheduler.interval_sec": cfg.interval_seconds,
                "scheduler.dry_run": cfg.dry_run,
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

        banano = BananoClient(node_url=cfg.node_url, dry_run=cfg.dry_run)
        with tracer.start_as_current_span(
            "operator_balance_check",
            attributes={
                "banano.node_url": cfg.node_url,
                "banano.min_balance": cfg.min_operator_balance_ban,
                "scheduler.dry_run": cfg.dry_run,
            },
        ):
            has_balance = banano.has_min_balance(cfg.min_operator_balance_ban, cfg.operator_account)
        if not has_balance:
            log.warning("settlement_skipped_low_balance")
            return
        with tracer.start_as_current_span(
            "settlement_cycle",
            attributes={
                "banano.min_balance": cfg.min_operator_balance_ban,
                "scheduler.interval_sec": cfg.interval_seconds,
            },
        ):
            run_settlement(session, cfg)
    except Exception as exc:  # pragma: no cover
        JOB_ERRORS.inc()
        log.error("settlement_cycle_error", error=str(exc))


def main() -> None:
    metrics_port = int(os.getenv("P2S_METRICS_PORT", "8001"))
    db_url = os.getenv("DATABASE_URL", "sqlite:///pay2slay.db")
    # Metrics server
    start_http_server(metrics_port)
    # DB
    engine = create_engine(db_url)
    session_local = sessionmaker(bind=engine)
    cfg, fortnite, accrual_cfg = _build_scheduler_components()
    jitter = float(os.getenv("P2S_START_JITTER_SEC", "0"))
    if jitter > 0:
        sleep_for = random.uniform(0, jitter)
        log.info("startup_jitter", sleep_for=round(sleep_for, 3))
        time.sleep(sleep_for)
    backoff = 1.0
    max_backoff = 60.0
    while True:  # pragma: no cover
        session: Session = session_local()
        try:
            _run_once(session, cfg, fortnite, accrual_cfg)
            backoff = 1.0  # reset after success path
        except Exception as loop_exc:  # pragma: no cover
            JOB_ERRORS.inc()
            log.error("scheduler_loop_error", error=str(loop_exc), backoff=backoff)
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
        finally:
            session.close()
        time.sleep(cfg.interval_seconds)


if __name__ == "__main__":  # pragma: no cover
    main()
