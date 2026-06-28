"""In-process ring buffer of recent log lines.

Lets the admin UI tail logs without shelling out to provider-services or
needing kubectl access on the Akash provider. Captures every record
the root logger sees (which is everything structlog routes through
the stdlib logging adapter).

Capacity is bounded so memory stays flat under load. Records are
emitted as JSON strings (matching structlog's JSONRenderer output)
so the UI can parse + colorize them.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections import deque
from collections.abc import AsyncIterator
from typing import Final

# Bounded ring of recent log lines. 5000 lines @ ~200 bytes each =
# ~1 MB in memory. Adjust via P2S_LOG_BUFFER_SIZE.
_DEFAULT_CAPACITY: Final[int] = 5000


class _RingBuffer:
    """Thread-safe append-only ring + async subscriber notification."""

    def __init__(self, capacity: int) -> None:
        self._buf: deque[str] = deque(maxlen=capacity)
        self._lock = threading.Lock()
        # Subscribers are asyncio.Queue instances; one per /admin/logs/tail caller.
        self._subscribers: set[asyncio.Queue[str]] = set()
        self._sub_lock = threading.Lock()
        # The event loop the API runs in. Set once at startup so the
        # logging handler (which may fire from a non-asyncio thread)
        # can safely poke subscribers.
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def append(self, line: str) -> None:
        with self._lock:
            self._buf.append(line)
        self._broadcast(line)

    def snapshot(self, tail: int | None = None) -> list[str]:
        with self._lock:
            if tail is None or tail >= len(self._buf):
                return list(self._buf)
            return list(self._buf)[-tail:]

    def _broadcast(self, line: str) -> None:
        """Push line to every subscriber queue. Safe from any thread."""
        loop = self._loop
        if loop is None:
            return
        with self._sub_lock:
            subs = list(self._subscribers)
        for q in subs:
            try:
                loop.call_soon_threadsafe(q.put_nowait, line)
            except Exception:
                # Subscriber went away, queue is full, or loop is dead.
                # Drop the line; subscriber will reconnect.
                pass

    def subscribe(self) -> asyncio.Queue[str]:
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=512)
        with self._sub_lock:
            self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[str]) -> None:
        with self._sub_lock:
            self._subscribers.discard(q)


class _BufferHandler(logging.Handler):
    """Logging handler that pushes every formatted record into the ring."""

    def __init__(self, ring: _RingBuffer) -> None:
        super().__init__()
        self._ring = ring

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            try:
                msg = record.getMessage()
            except Exception:
                return
        self._ring.append(msg)


# Singleton state lives on a holder class so install() doesn't need
# `global` (ruff PLW0603). Tests can patch attributes directly.
class _State:
    ring: _RingBuffer | None = None
    handler: _BufferHandler | None = None


def install(capacity: int = _DEFAULT_CAPACITY) -> _RingBuffer:
    """Attach the ring buffer handler to the root logger. Idempotent.

    Also lowers the root logger's level to INFO if it's still at the
    stdlib default (WARNING). Apps that call setup_structlog before us
    will already have it lower; this is just a safety net for tests
    and direct CLI invocations.
    """
    if _State.ring is not None:
        return _State.ring
    _State.ring = _RingBuffer(capacity=capacity)
    _State.handler = _BufferHandler(_State.ring)
    _State.handler.setLevel(logging.DEBUG)
    # Match structlog's output — the structlog adapter formats via the
    # root logger's message, which is already a JSON string when
    # setup_structlog ran. Use a plain %(message)s formatter so we
    # don't double-format.
    _State.handler.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger()
    root.addHandler(_State.handler)
    # Stdlib default for the root logger is WARNING. The buffer needs to
    # see INFO at least; setup_structlog overrides if it ran first.
    if root.level > logging.INFO or root.level == logging.NOTSET:
        root.setLevel(logging.INFO)
    return _State.ring


def get_ring() -> _RingBuffer:
    """Return the installed ring buffer, installing on first use."""
    if _State.ring is None:
        return install()
    return _State.ring


def attach_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Call from FastAPI startup so cross-thread broadcasts work."""
    get_ring().set_loop(loop)


async def stream(tail: int = 200) -> AsyncIterator[str]:
    """Yield the last `tail` lines from the buffer, then stream new lines
    as they arrive. Caller iterates until they disconnect.
    """
    ring = get_ring()
    # Replay tail first
    for line in ring.snapshot(tail=tail):
        yield line
    # Then live-stream
    queue = ring.subscribe()
    try:
        while True:
            line = await queue.get()
            yield line
    finally:
        ring.unsubscribe(queue)
