# T053 foreign repo rejection (initial failing)
import pytest

ALLOWED_PREFIXES = ["ghcr.io/mconstant/pay2slay-api", "ghcr.io/mconstant/pay2slay-api-staging"]


class ForeignRepositoryError(Exception):
    pass


def ensure_repo_allowed(repo: str):
    if not any(repo.startswith(p) for p in ALLOWED_PREFIXES):
        raise ForeignRepositoryError(repo)


def test_foreign_repo_rejected():
    with pytest.raises(ForeignRepositoryError):
        ensure_repo_allowed("ghcr.io/attacker/other")


def test_legit_repo():
    # Allowed repo should NOT raise
    ensure_repo_allowed("ghcr.io/mconstant/pay2slay-api")
