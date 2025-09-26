#!/usr/bin/env python3
"""Emit image build metadata as JSON (T012, T056).

Fields (initial spec):
  image_sha (40 hex)
  short_sha (12 chars)
  repository
  repository_type (canonical|staging|unknown)
  image_digest
  signature_status (verified|unverified)
  signature_reason (string)
  arch (e.g. linux/amd64) - single arch per FR-015
  build_duration_sec (float)
  pre_push_digest (optional placeholder until populated by workflow)
  post_push_digest (optional placeholder until populated by workflow)
  digest_verification (status placeholder: unknown|ok|mismatch)

Usage:
  emit_image_metadata.py --sha <40-hex> --repository ghcr.io/... --digest sha256:... \
      [--signature-status verified --signature-reason n/a] [--arch linux/amd64]

Unknown fields may be filled by later workflow steps; placeholders keep contract keys present so
contract tests can evolve toward passing once real values wired.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass

SHA_LENGTH = 40  # constant for git SHA length (lint: magic number)

# Minimal validation helpers duplicated until image_artifact module imported (circular-safe)


def _validate_sha(tag: str) -> None:
    if len(tag) != SHA_LENGTH or any(c not in "0123456789abcdef" for c in tag):
        raise ValueError(f"Invalid git sha: {tag}")


def _short_sha(tag: str) -> str:
    return tag[:12]


def detect_arch() -> str:
    # Single arch constraint; allow override for future flexibility
    return os.getenv("PAY2SLAY_BUILD_ARCH", "linux/amd64")


def infer_repository_type(repository: str) -> str:
    if repository.endswith("-staging"):
        return "staging"
    if repository.rsplit("/", 1)[-1].endswith("pay2slay-api"):
        return "canonical"
    return "unknown"


@dataclass
class ImageMetadata:
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
    digest_verification: str | None = None  # ok|mismatch|unknown


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sha", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--signature-status", default="unverified")
    parser.add_argument("--signature-reason", default="missing")
    parser.add_argument("--arch", default=None)
    parser.add_argument(
        "--start-time",
        type=float,
        default=None,
        help="Epoch start time for build to compute duration",
    )
    args = parser.parse_args(argv)

    _validate_sha(args.sha)
    start_time = args.start_time if args.start_time is not None else time.time()
    # Simulate build work already done; duration is now - start
    duration = max(0.0, time.time() - start_time)

    arch = args.arch or detect_arch()
    metadata = ImageMetadata(
        image_sha=args.sha,
        short_sha=_short_sha(args.sha),
        repository=args.repository,
        repository_type=infer_repository_type(args.repository),
        image_digest=args.digest,
        signature_status=args.signature_status,
        signature_reason=args.signature_reason,
        arch=arch,
        build_duration_sec=duration,
        pre_push_digest=None,
        post_push_digest=None,
        digest_verification="unknown",
    )
    json.dump(asdict(metadata), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
