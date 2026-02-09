"""Encryption utilities for secure config storage.

Uses Fernet symmetric encryption derived from SESSION_SECRET.
"""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken  # type: ignore[import-not-found]

# Banano seed is 64 hex characters (32 bytes)
BANANO_SEED_HEX_LEN = 64


def _get_fernet_key(secret: str) -> bytes:
    """Derive a 32-byte Fernet key from the session secret."""
    # Use SHA-256 to get consistent 32 bytes, then base64 encode for Fernet
    key_bytes = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key_bytes)


def _get_fernet() -> Fernet:
    """Get Fernet instance using SESSION_SECRET."""
    secret = os.getenv("SESSION_SECRET", "dev-secret")
    return Fernet(_get_fernet_key(secret))


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value, return base64-encoded ciphertext."""
    f = _get_fernet()
    ciphertext = f.encrypt(plaintext.encode("utf-8"))
    return str(ciphertext.decode("ascii"))


def decrypt_value(ciphertext: str) -> str | None:
    """Decrypt a base64-encoded ciphertext, return plaintext or None if invalid."""
    try:
        f = _get_fernet()
        plaintext = f.decrypt(ciphertext.encode("ascii"))
        return str(plaintext.decode("utf-8"))
    except InvalidToken:
        return None


def validate_banano_seed(seed: str) -> bool:
    """Validate a Banano seed (64 hex characters)."""
    if len(seed) != BANANO_SEED_HEX_LEN:
        return False
    try:
        int(seed, 16)
        return True
    except ValueError:
        return False
