"""Deployment validation stubs (T014, seeds for security tasks T029, T057).

Current behavior is intentionally simplistic to satisfy early tests once wired:
- ensure_tag_exists: raises MissingImageTagError when simulated missing (sha endswith 'deadbeef').
- ensure_repo_allowed: canonical vs staging mapping (FR-016); main branch must use canonical repo.

Future enhancements: registry API checks, digest comparison (T028 deployment-time guard), floating tag rejection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


class MissingImageTagError(Exception):
    pass


class RepositoryPolicyError(Exception):
    pass


class FloatingTagError(Exception):
    pass


ALLOWED_CANONICAL_SUFFIX = "pay2slay-api"


def ensure_tag_exists(repo: str, sha: str) -> None:
    # Placeholder sentinel: if SHA artificially ends with 'deadbeef' treat as missing
    if sha.endswith("deadbeef"):
        raise MissingImageTagError(f"Tag {sha} not found in {repo}")


def ensure_repo_allowed(repo: str, is_main: bool) -> None:
    if is_main:
        # main must target canonical (not -staging)
        if repo.endswith("-staging"):
            raise RepositoryPolicyError("main branch must deploy to canonical repo")
        if not repo.endswith(ALLOWED_CANONICAL_SUFFIX):
            raise RepositoryPolicyError("Unexpected canonical repo name")
    # Non-main should use staging repo variant
    elif not repo.endswith("-staging"):
        raise RepositoryPolicyError("feature branch must deploy to staging repo")


FLOATING_TAG_PATTERN = re.compile(r":(latest|main|stable)$")


def reject_floating_tag(image_ref: str) -> None:
    if FLOATING_TAG_PATTERN.search(image_ref):
        raise FloatingTagError(f"Floating tag rejected: {image_ref}")


@dataclass
class DeployContext:
    repository: str
    image_sha: str
    is_main: bool

    def validate(self) -> None:
        ensure_tag_exists(self.repository, self.image_sha)
        ensure_repo_allowed(self.repository, self.is_main)
