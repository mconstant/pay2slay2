"""Image artifact helper functions (T013, supports T012, future workflow integration).

This module centralizes logic around git SHA validation, short SHA derivation, and build
metadata assembly to keep scripts thin.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass

SHA_LENGTH = 40  # git SHA length constant (avoid magic number)


class InvalidGitShaError(ValueError):
    pass


def validate_sha_tag(tag: str) -> None:
    if len(tag) != SHA_LENGTH or any(c not in "0123456789abcdef" for c in tag):
        raise InvalidGitShaError(f"Invalid git sha: {tag}")


def calc_short_sha(tag: str) -> str:
    validate_sha_tag(tag)
    return tag[:12]


@dataclass
class BuildMetadata:
    image_sha: str
    short_sha: str
    repository: str
    repository_type: str
    image_digest: str
    signature_status: str
    signature_reason: str
    arch: str
    build_duration_sec: float
    pre_push_digest: str | None = None
    post_push_digest: str | None = None
    digest_verification: str | None = None


@dataclass
class BuildParams:
    git_sha: str
    repo: str
    digest: str
    signature_status: str
    start_time: float
    signature_reason: str = "missing"
    arch: str = "linux/amd64"


def build_metadata(params: BuildParams) -> dict[str, object]:
    validate_sha_tag(params.git_sha)
    duration = max(0.0, time.time() - params.start_time)
    repository_type = (
        "staging"
        if params.repo.endswith("-staging")
        else ("canonical" if params.repo.endswith("pay2slay-api") else "unknown")
    )
    meta = BuildMetadata(
        image_sha=params.git_sha,
        short_sha=calc_short_sha(params.git_sha),
        repository=params.repo,
        repository_type=repository_type,
        image_digest=params.digest,
        signature_status=params.signature_status,
        signature_reason=params.signature_reason,
        arch=params.arch,
        build_duration_sec=duration,
        pre_push_digest=None,
        post_push_digest=None,
        digest_verification="unknown",
    )
    return asdict(meta)
