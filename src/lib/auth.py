from __future__ import annotations

import base64
import hmac
import json
import os
import time
from hashlib import sha256
from secrets import token_urlsafe
from typing import Any, cast

# In-memory replay cache container (mutable dict to avoid needing 'global')
_OAUTH_REPLAY_STATE: dict[str, Any] = {
    "cache": {},  # nonce -> exp timestamp
    "last_clean": 0.0,
    "interval": 30,  # seconds between GC passes
}


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def issue_session(discord_user_id: str, secret: str, ttl_seconds: int = 86400) -> str:
    payload = {
        "uid": discord_user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl_seconds,
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), body, sha256).digest()
    return f"{_b64url(body)}.{_b64url(sig)}"


def verify_session(token: str, secret: str) -> str | None:
    try:
        body_b64, sig_b64 = token.split(".", 1)
        body = _b64url_decode(body_b64)
        sig = _b64url_decode(sig_b64)
        good = hmac.new(secret.encode("utf-8"), body, sha256).digest()
        if not hmac.compare_digest(sig, good):
            return None
        raw = json.loads(body)
        if not isinstance(raw, dict):
            return None
        payload: dict[str, Any] = raw  # narrow type for mypy
        if payload.get("exp", 0) < int(time.time()):
            return None
        uid = payload.get("uid")
        return str(uid) if uid is not None else None
    except Exception:
        return None


def session_secret() -> str:
    return os.getenv("SESSION_SECRET", "dev-secret")


# OAuth state / nonce utilities
def issue_oauth_state(secret: str, ttl_seconds: int = 600) -> str:
    """Issue a signed ephemeral OAuth state token (HMAC)."""
    payload = {
        "nonce": token_urlsafe(8),
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl_seconds,
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), body, sha256).digest()
    return f"{_b64url(body)}.{_b64url(sig)}"


def _decode_oauth_state(token: str, secret: str) -> dict[str, Any] | None:
    """Decode + verify signature & expiry. Returns payload or None."""
    try:
        body_b64, sig_b64 = token.split(".", 1)
        body = _b64url_decode(body_b64)
        sig = _b64url_decode(sig_b64)
        good = hmac.new(secret.encode("utf-8"), body, sha256).digest()
        if not hmac.compare_digest(sig, good):  # signature mismatch
            return None
        raw = json.loads(body)
        if not isinstance(raw, dict):  # ensure mapping
            return None
        payload: dict[str, Any] = raw
        if payload.get("exp", 0) < int(time.time()):  # expired
            return None
        if "nonce" not in payload:
            return None
        return payload
    except Exception:
        return None


def verify_oauth_state(token: str, secret: str) -> bool:  # backward-compatible (no replay)
    return _decode_oauth_state(token, secret) is not None


def consume_oauth_state(token: str, secret: str, enforce_single_use: bool = True) -> bool:
    """Verify & optionally enforce single-use semantics for OAuth state tokens.

    When enforce_single_use=True (default), a nonce may only be consumed once
    per process lifetime (until its natural expiry). Subsequent attempts are rejected.
    """
    payload = _decode_oauth_state(token, secret)
    if not payload:
        return False
    nonce: str = str(payload["nonce"])
    exp: int = int(payload.get("exp", 0))
    now = time.time()
    if enforce_single_use:
        # Opportunistic GC of expired entries
        if now - _OAUTH_REPLAY_STATE["last_clean"] > _OAUTH_REPLAY_STATE["interval"]:
            _OAUTH_REPLAY_STATE["last_clean"] = now
            cache = cast(dict[str, int], _OAUTH_REPLAY_STATE["cache"])
            expired = [k for k, v in cache.items() if v < now]
            for k in expired:
                cache.pop(k, None)
        cache = cast(dict[str, int], _OAUTH_REPLAY_STATE["cache"])
        if nonce in cache:  # replay attempt
            return False
        cache[nonce] = exp
    return True


__all__ = [
    # existing exports
    "issue_session",
    "verify_session",
    "session_secret",
    "issue_oauth_state",
    "verify_oauth_state",
    "consume_oauth_state",
    "issue_admin_session",
    "verify_admin_session",
]


# Admin sessions
def issue_admin_session(admin_email: str, secret: str, ttl_seconds: int = 3600) -> str:
    payload = {
        "role": "admin",
        "email": admin_email,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl_seconds,
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), body, sha256).digest()
    return f"{_b64url(body)}.{_b64url(sig)}"


def verify_admin_session(token: str, secret: str) -> str | None:
    try:
        body_b64, sig_b64 = token.split(".", 1)
        body = _b64url_decode(body_b64)
        sig = _b64url_decode(sig_b64)
        good = hmac.new(secret.encode("utf-8"), body, sha256).digest()
        if not hmac.compare_digest(sig, good):
            return None
        payload = json.loads(body)
        if payload.get("exp", 0) < int(time.time()):
            return None
        if payload.get("role") != "admin":
            return None
        email = payload.get("email")
        return str(email) if email is not None else None
    except Exception:
        return None
