from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from prometheus_client import Counter, start_http_server

HEARTBEAT_PATH = Path(os.getenv("P2S_HEARTBEAT_FILE", "/tmp/scheduler_heartbeat.json"))
SCHEDULER_CONFIG_PATH = Path(
    os.getenv("P2S_SCHEDULER_CONFIG_FILE", "/tmp/scheduler_overrides.json")
)

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


def _read_scheduler_overrides(default_interval: int) -> dict[str, int]:
    """Read admin-set interval overrides from the shared config file."""
    result = {
        "accrual_interval_seconds": default_interval,
        "settlement_interval_seconds": default_interval,
    }
    if not SCHEDULER_CONFIG_PATH.exists():
        return result
    try:
        data = json.loads(SCHEDULER_CONFIG_PATH.read_text())
        if "accrual_interval_seconds" in data:
            result["accrual_interval_seconds"] = max(30, int(data["accrual_interval_seconds"]))
        if "settlement_interval_seconds" in data:
            result["settlement_interval_seconds"] = max(
                30, int(data["settlement_interval_seconds"])
            )
    except Exception:
        pass
    return result


@dataclass
class HeartbeatInfo:
    """Collects all heartbeat fields to avoid arg bloat."""

    status: str = "ok"
    error: str | None = None
    accrual_interval: int = 0
    settlement_interval: int = 0
    last_accrual_ts: float = 0.0
    last_settlement_ts: float = 0.0


def _write_heartbeat(hb: HeartbeatInfo) -> None:
    """Write scheduler heartbeat to a shared file the API can read."""
    try:
        data: dict[str, object] = {
            "ts": time.time(),
            "status": hb.status,
            "pid": os.getpid(),
            "accrual_interval_seconds": hb.accrual_interval,
            "settlement_interval_seconds": hb.settlement_interval,
            "interval_seconds": hb.accrual_interval,  # backward compat
            "last_accrual_ts": hb.last_accrual_ts,
            "last_settlement_ts": hb.last_settlement_ts,
        }
        if hb.error:
            data["error"] = hb.error[:500]
        HEARTBEAT_PATH.write_text(json.dumps(data))
    except Exception:
        pass  # best-effort


def _run_accrual_only(
    session: Session,
    scheduler_cfg: SchedulerConfig,
    fortnite: FortniteService,
    accrual_cfg: AccrualJobConfig,
) -> None:
    """Run only the accrual phase."""
    tracer = get_tracer("scheduler")
    try:
        with tracer.start_as_current_span(
            "accrual_cycle",
            attributes={
                "scheduler.interval_sec": scheduler_cfg.interval_seconds,
                "scheduler.dry_run": scheduler_cfg.dry_run,
                "fortnite.base_url": fortnite.base_url,
            },
        ):
            accrual_res = run_accrual(session, fortnite, accrual_cfg)
            log.info("accrual_cycle", **accrual_res)
    except Exception as exc:  # pragma: no cover
        JOB_ERRORS.inc()
        log.error("accrual_cycle_error", error=str(exc))


def _run_settlement_only(
    session: Session,
    scheduler_cfg: SchedulerConfig,
) -> None:
    """Run only the settlement phase."""
    tracer = get_tracer("scheduler")
    cfg = scheduler_cfg
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


@dataclass
class _LoopState:
    """Mutable state for the scheduler loop."""

    last_accrual_ts: float = 0.0
    last_settlement_ts: float = 0.0
    backoff: float = 1.0


def _scheduler_loop(
    session_local: sessionmaker[Session],
    cfg: SchedulerConfig,
    fortnite: FortniteService,
    accrual_cfg: AccrualJobConfig,
    state: _LoopState,
) -> None:  # pragma: no cover
    """Run one tick of the scheduler loop (hot-reloads intervals)."""
    overrides = _read_scheduler_overrides(cfg.interval_seconds)
    accrual_iv = overrides["accrual_interval_seconds"]
    settlement_iv = overrides["settlement_interval_seconds"]

    now = time.time()
    run_accrual_now = (now - state.last_accrual_ts) >= accrual_iv
    run_settle_now = (now - state.last_settlement_ts) >= settlement_iv

    if not run_accrual_now and not run_settle_now:
        next_a = state.last_accrual_ts + accrual_iv - now
        next_s = state.last_settlement_ts + settlement_iv - now
        time.sleep(max(1, min(next_a, next_s)))
        return

    session: Session = session_local()
    try:
        if run_accrual_now:
            _run_accrual_only(session, cfg, fortnite, accrual_cfg)
            state.last_accrual_ts = time.time()
        if run_settle_now:
            _run_settlement_only(session, cfg)
            state.last_settlement_ts = time.time()
        _write_heartbeat(
            HeartbeatInfo(
                accrual_interval=accrual_iv,
                settlement_interval=settlement_iv,
                last_accrual_ts=state.last_accrual_ts,
                last_settlement_ts=state.last_settlement_ts,
            )
        )
        state.backoff = 1.0
    except Exception as exc:
        JOB_ERRORS.inc()
        log.error("scheduler_loop_error", error=str(exc), backoff=state.backoff)
        _write_heartbeat(
            HeartbeatInfo(
                status="error",
                error=str(exc),
                accrual_interval=accrual_iv,
                settlement_interval=settlement_iv,
                last_accrual_ts=state.last_accrual_ts,
                last_settlement_ts=state.last_settlement_ts,
            )
        )
        time.sleep(state.backoff)
        state.backoff = min(state.backoff * 2, 60.0)
    finally:
        session.close()


def main() -> None:
    metrics_port = int(os.getenv("P2S_METRICS_PORT", "8001"))
    db_url = os.getenv("DATABASE_URL", "sqlite:///pay2slay.db")
    start_http_server(metrics_port)
    engine = create_engine(db_url)
    session_local = sessionmaker(bind=engine)
    cfg, fortnite, accrual_cfg = _build_scheduler_components()
    overrides = _read_scheduler_overrides(cfg.interval_seconds)
    _write_heartbeat(
        HeartbeatInfo(
            status="started",
            accrual_interval=overrides["accrual_interval_seconds"],
            settlement_interval=overrides["settlement_interval_seconds"],
        )
    )
    log.info(
        "scheduler_started",
        accrual_interval=overrides["accrual_interval_seconds"],
        settlement_interval=overrides["settlement_interval_seconds"],
        dry_run=cfg.dry_run,
    )
    jitter = float(os.getenv("P2S_START_JITTER_SEC", "0"))
    if jitter > 0:
        sleep_for = random.uniform(0, jitter)
        log.info("startup_jitter", sleep_for=round(sleep_for, 3))
        time.sleep(sleep_for)
    state = _LoopState()
    # Offset settlement by half the interval so accruals get settled
    # mid-cycle (~10 min) instead of waiting a full cycle (~20 min).
    state.last_settlement_ts = time.time() - overrides["settlement_interval_seconds"] / 2
    while True:  # pragma: no cover
        _scheduler_loop(session_local, cfg, fortnite, accrual_cfg, state)


if __name__ == "__main__":  # pragma: no cover
    main()
