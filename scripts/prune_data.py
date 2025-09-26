"""T070: Data retention pruning placeholder.

Intended to prune old accrual, payout, and audit rows based on retention policy.
Currently a no-op with logging scaffolding.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.lib.config import get_config
from src.lib.db import make_engine, make_session_factory
from src.lib.observability import get_logger
from src.models import models  # noqa: F401
from src.models.base import Base

LOG = get_logger(__name__)


def prune(retention_days: int = 90) -> None:  # pragma: no cover (placeholder)
    cfg = get_config()
    engine = make_engine(cfg.database_url)
    Base.metadata.create_all(bind=engine)
    session_factory = make_session_factory(engine)
    session = session_factory()
    try:
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        LOG.info("prune_start", cutoff=str(cutoff.date()))
        # TODO: Implement deletion logic for RewardAccrual, Payout, AdminAudit older than cutoff
        LOG.info("prune_complete", deleted_counts={})
    finally:
        session.close()


if __name__ == "__main__":  # pragma: no cover
    prune()
