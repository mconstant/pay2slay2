# T038 negative digest mismatch test (initial failing)
import pytest


class DigestMismatchError(Exception):
    pass


def compare_digests(local: str, remote: str):
    if local != remote:
        raise DigestMismatchError("Digest mismatch")


def test_digest_mismatch_raises():
    with pytest.raises(DigestMismatchError):
        compare_digests("sha256:" + "a" * 64, "sha256:" + "b" * 64)
