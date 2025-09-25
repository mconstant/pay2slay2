from sqlalchemy.orm import Session

from src.lib.config import get_config
from src.models.models import Payout, RewardAccrual, User, WalletLink
from src.services.banano_client import BananoClient
from src.services.domain.accrual_service import AccrualService
from src.services.domain.payout_service import PayoutService
from src.services.domain.settlement_service import SettlementService
from src.services.fortnite_service import FortniteService, KillsDelta

KILL_DELTA = 7
FLOAT_TOL = 1e-6


class PositiveDeltaFortnite(FortniteService):
    def __init__(self, delta: int):  # type: ignore[super-init-not-called]
        self._delta = delta
        self._cursor_base = 0

    def get_kills_since(self, epic_account_id: str, cursor: str | None):  # type: ignore[override]
        prev = int(cursor) if cursor and cursor.isdigit() else 0
        return KillsDelta(
            epic_account_id=epic_account_id,
            since_cursor=cursor,
            new_cursor=str(prev + self._delta),
            kills=self._delta,
        )


def test_accrual_settlement_payout_flow(app, db_session: Session):  # type: ignore[override]
    cfg = get_config()
    # Seed a user as if they authenticated and linked a wallet
    user = User(
        discord_user_id="int_accrual_user", discord_guild_member=True, epic_account_id="epic_int"
    )
    db_session.add(user)
    db_session.flush()
    wl = WalletLink(user_id=user.id, address="ban_1flowwallet", is_primary=True, verified=True)
    db_session.add(wl)
    db_session.commit()

    # Accrual: simulate positive kill delta
    accrual_svc = AccrualService(
        db_session, PositiveDeltaFortnite(delta=KILL_DELTA), cfg.payout.payout_amount_ban_per_kill
    )
    res = accrual_svc.accrue_for_user(user)
    assert res is not None
    assert res.kills_delta == KILL_DELTA
    assert res.created is True

    db_session.commit()

    # Settlement candidate selection
    settle_svc = SettlementService(
        db_session, daily_cap=cfg.payout.daily_payout_cap, weekly_cap=cfg.payout.weekly_payout_cap
    )
    cands = settle_svc.select_candidates(limit=10)
    assert any(c.user.id == user.id for c in cands)
    cand = next(c for c in cands if c.user.id == user.id)
    assert abs((cand.payable_amount_ban or 0) - res.amount_ban) < FLOAT_TOL

    # Payout (dry-run Banano client)
    class DryBan(BananoClient):
        def __init__(self):  # type: ignore[super-init-not-called]
            self.sent = []

        def send(self, source_wallet: str, to_address: str, amount_raw: str):  # type: ignore[override]
            self.sent.append((source_wallet, to_address, amount_raw))
            return "dryrun_tx_hash"

    payout_svc = PayoutService(db_session, banano=DryBan(), dry_run=False)

    # Gather accrual rows
    accruals = (
        db_session.query(RewardAccrual)
        .filter(RewardAccrual.user_id == user.id, ~RewardAccrual.settled)
        .all()
    )
    assert accruals
    payout_res = payout_svc.create_payout(user, cand.payable_amount_ban or 0.0, accruals)
    assert payout_res is not None
    db_session.commit()

    # Assertions: payout row exists & accruals marked settled
    payout = db_session.query(Payout).filter(Payout.user_id == user.id).one_or_none()
    assert payout is not None
    assert payout.status in ("sent", "pending")
    refreshed_accruals = (
        db_session.query(RewardAccrual).filter(RewardAccrual.user_id == user.id).all()
    )
    assert all(a.settled for a in refreshed_accruals)
    # Cursor advanced
    updated_user = db_session.query(User).filter(User.id == user.id).one()
    assert updated_user.last_settled_kill_count >= KILL_DELTA
