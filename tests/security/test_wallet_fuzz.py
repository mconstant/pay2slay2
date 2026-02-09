from http import HTTPStatus

from sqlalchemy import select

INVALID_ADDRESSES = [
    "",  # empty
    "ban",  # too short & missing underscore
    "banX_1foo",  # wrong prefix
    "nan_1something",  # different currency style
    "ban_ whitespace",  # space (should be rejected now by whitespace rule)
    "ban_@!#$%",  # symbols
    "ban_1too_short",  # short body (<20)
    "ban_" + "1" * 200,  # excessively long
]


def test_wallet_address_fuzz_invalid_rejections(client, db_session):
    from src.models.models import User, WalletLink  # type: ignore

    client.get("/auth/discord/callback?state=xyz&code=dummy")
    # Snapshot baseline wallet link count (could be >0 if other tests created one)
    uid_row = db_session.execute(select(User.id)).first()
    user_id = uid_row[0] if uid_row else None
    baseline_count = 0
    if user_id:
        baseline_count = len(
            db_session.execute(select(WalletLink).where(WalletLink.user_id == user_id)).all()
        )
    for addr in INVALID_ADDRESSES:
        resp = client.post("/link/wallet", json={"banano_address": addr})
        assert resp.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY), addr

    # Ensure no additional wallet links created by invalid attempts
    if user_id:
        wl_after = db_session.execute(select(WalletLink).where(WalletLink.user_id == user_id)).all()
        assert len(wl_after) == baseline_count

    # Now a valid link works (length ok, no whitespace)
    good = client.post(
        "/link/wallet",
        json={"banano_address": "ban_1validexamplewalletaddresslongenough"},
    )
    assert good.status_code == HTTPStatus.OK
