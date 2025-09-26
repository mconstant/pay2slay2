"""Rollback logic stubs (T015) with build invocation sentinel (T040).

Provides:
- record_rollback(previous_sha, new_sha)
- get_rollbacks()
- set_build_invocation() only used internally to detect forbidden calls.

Environment variable PAY2SLAY_ROLLBACK_SENTINEL=1 enables strict sentinel raising if a build is attempted
within rollback context (future integration). For now, tests can monkeypatch attempt_build() to ensure
no call occurs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class RollbackBuildInvocationError(RuntimeError):
    pass


@dataclass
class RollbackEvent:
    previous_sha: str
    image_sha: str


class _RollbackState:
    def __init__(self) -> None:
        self._events: list[RollbackEvent] = []
        self._build_called = False

    def attempt_build(self) -> None:
        self._build_called = True
        if os.getenv("PAY2SLAY_ROLLBACK_SENTINEL") == "1":
            raise RollbackBuildInvocationError("Build attempted during rollback")

    def record(self, previous_sha: str, new_sha: str) -> RollbackEvent:
        event = RollbackEvent(previous_sha=previous_sha, image_sha=new_sha)
        self._events.append(event)
        return event

    def events(self) -> list[RollbackEvent]:
        return list(self._events)

    def build_called(self) -> bool:
        return self._build_called


_STATE = _RollbackState()


def attempt_build_during_rollback() -> None:
    _STATE.attempt_build()


def record_rollback(previous_sha: str, new_sha: str) -> RollbackEvent:
    return _STATE.record(previous_sha, new_sha)


def get_rollbacks() -> list[RollbackEvent]:
    return _STATE.events()


def build_was_called() -> bool:
    return _STATE.build_called()
