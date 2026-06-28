"""Contract tests for the admin log-tail endpoints."""

from __future__ import annotations

import logging

HTTP_UNAUTHORIZED = 401
TAIL_BOUND = 5


def test_admin_logs_recent_requires_auth(client) -> None:
    r = client.get("/admin/logs/recent")
    assert r.status_code == HTTP_UNAUTHORIZED


def test_admin_logs_tail_requires_auth(client) -> None:
    r = client.get("/admin/logs/tail")
    assert r.status_code == HTTP_UNAUTHORIZED


def test_log_buffer_install_idempotent() -> None:
    """install() must be safe to call twice (e.g. across test app re-creation)."""
    from src.lib import log_buffer

    ring1 = log_buffer.install(capacity=100)
    ring2 = log_buffer.install(capacity=100)
    assert ring1 is ring2


def test_log_buffer_captures_logs_via_handler() -> None:
    """The ring handler should capture log records dispatched to root.

    We invoke the handler directly here because pytest's caplog plugin
    sometimes intercepts at logger.handle() before our handler runs.
    Real-world (FastAPI process) the handler is the terminal sink and
    captures everything; this test verifies the formatting + storage.
    """
    from src.lib import log_buffer

    # Re-attach handler if conftest's app fixture replaced it with basicConfig.
    ring = log_buffer.install(capacity=100)
    root = logging.getLogger()
    our_handler = next(
        (h for h in root.handlers if h.__class__.__name__ == "_BufferHandler"),
        None,
    )
    if our_handler is None:
        # The conftest's basicConfig wiped us — re-install fresh and re-attach.
        # We can't reset the module-level singleton trivially; just create a
        # fresh handler tied to the same ring.
        from src.lib.log_buffer import _BufferHandler  # type: ignore[attr-defined]

        our_handler = _BufferHandler(ring)
        our_handler.setLevel(logging.DEBUG)
        our_handler.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(our_handler)
    record = logging.LogRecord(
        name="test.log_buffer",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="pytest-log-ring-token-92716",
        args=(),
        exc_info=None,
    )
    our_handler.emit(record)
    lines = ring.snapshot(tail=50)
    assert any(
        "pytest-log-ring-token-92716" in line for line in lines
    ), f"expected token in ring, got tail: {lines[-3:]}"


def test_log_buffer_snapshot_tail_bounded() -> None:
    """Snapshot tail must clip to requested size."""
    from src.lib import log_buffer

    ring = log_buffer.install(capacity=100)
    # Direct .append guarantees stable behavior independent of stdlib
    # logging level / pytest interception.
    for i in range(30):
        ring.append(f"line-{i}")
    s = ring.snapshot(tail=TAIL_BOUND)
    assert len(s) == TAIL_BOUND
    assert s[-1] == "line-29"
