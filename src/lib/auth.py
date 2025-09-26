from __future__ import annotations

import base64
import hmac
import json
import os
import time
from hashlib import sha256
from secrets import token_urlsafe


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
        payload = json.loads(body)
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


def verify_oauth_state(token: str, secret: str) -> bool:
    try:
        body_b64, sig_b64 = token.split(".", 1)
        body = _b64url_decode(body_b64)
        sig = _b64url_decode(sig_b64)
        good = hmac.new(secret.encode("utf-8"), body, sha256).digest()
        if not hmac.compare_digest(sig, good):
            return False
        payload = json.loads(body)
        if payload.get("exp", 0) < int(time.time()):
            return False
        return True
    except Exception:
        return False


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
