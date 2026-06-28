"""Contract tests for the operator-seed dedupe endpoint + dedupe-safe lookups.

Covers the bug surfaced 2026-06-28: alembic drift allowed two
`operator_seed` rows to coexist; `one_or_none()` then crashed settlement
with `MultipleResultsFound`. The fix switches every read to
`order_by(id desc).first()` and exposes an admin endpoint that
collapses dupes.
"""

from __future__ import annotations

HTTP_UNAUTHORIZED = 401


def test_dedupe_endpoint_requires_auth(client) -> None:
    r = client.post("/admin/config/operator-seed/dedupe")
    assert r.status_code == HTTP_UNAUTHORIZED


def test_load_operator_seed_survives_duplicate_rows(db_session) -> None:
    """Confirm the settlement-side loader picks the newest row, no crash.

    Production picked up two rows for `operator_seed` despite the
    declared UNIQUE constraint, because alembic drift skipped the index
    creation. We simulate that here by inserting via raw SQL — which
    bypasses the SQLAlchemy-level UNIQUE check.
    """
    from sqlalchemy import text

    from src.jobs.settlement import _load_operator_seed
    from src.lib.crypto import encrypt_value

    # Drop the UNIQUE index that the test schema has, to mirror prod drift.
    db_session.execute(text("DROP INDEX IF EXISTS ix_secure_config_key"))
    db_session.execute(
        text(
            "INSERT INTO secure_config (key, encrypted_value, set_by, description) "
            "VALUES (:k, :v, :b, :d)"
        ),
        {"k": "operator_seed", "v": encrypt_value("a" * 64), "b": "old", "d": "stale"},
    )
    db_session.execute(
        text(
            "INSERT INTO secure_config (key, encrypted_value, set_by, description) "
            "VALUES (:k, :v, :b, :d)"
        ),
        {"k": "operator_seed", "v": encrypt_value("b" * 64), "b": "new", "d": "latest"},
    )
    db_session.commit()
    seed = _load_operator_seed(db_session)
    assert seed == "b" * 64
