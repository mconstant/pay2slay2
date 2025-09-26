from sqlalchemy.orm import Session

try:  # pragma: no cover - test environment path guard
    from src.lib.config import get_config  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from src.lib.config import get_config  # type: ignore

from src.models.models import User
from src.services.domain.accrual_service import AccrualService
from src.services.fortnite_service import FortniteService, KillsDelta

DELTA = 3
ZERO = 0


class ExhaustingFortnite(FortniteService):
    def __init__(self):  # type: ignore[super-init-not-called]
        self._served = False
        self._dry_run = False
        self.per_minute_limit = 1

    def get_kills_since(self, epic_account_id: str, cursor: str | None):  # type: ignore[override]
        # First invocation returns DELTA relative to cursor; subsequent invocations simulate rate-limit => zero
        if not self._served:
            self._served = True
            base = int(cursor) if cursor and cursor.isdigit() else 0
            new_total = base + DELTA
            return KillsDelta(
                epic_account_id=epic_account_id,
                since_cursor=cursor,
                new_cursor=str(new_total),
                kills=DELTA,
            )
        return KillsDelta(
            epic_account_id=epic_account_id,
            since_cursor=cursor,
            new_cursor=cursor,
            kills=ZERO,
        )


def test_rate_limit_exhaustion_accrual(db_session: Session):  # type: ignore[override]
    cfg = get_config()
    user = User(discord_user_id="rl_user", discord_guild_member=True, epic_account_id="epic_rl")
    db_session.add(user)
    db_session.commit()
    svc = AccrualService(db_session, ExhaustingFortnite(), cfg.payout.payout_amount_ban_per_kill)
    first = svc.accrue_for_user(user)
    second = svc.accrue_for_user(user)
    assert first and first.kills_delta == DELTA and first.created
    assert second and second.kills_delta == ZERO and not second.created
