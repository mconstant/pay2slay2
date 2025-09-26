#!/usr/bin/env python3
"""Deployment-time digest & repository guard (T028, refined by T043).

Compares recorded digest from build metadata with live registry digest for an IMAGE_SHA tag.
Also enforces repository mapping policy (canonical for main, staging for non-main) as defense-in-depth.

Current implementation is a stub that re-uses the pre-recorded digest (no real registry call yet),
allowing tests to be written now. Future enhancement: invoke `docker pull` then `docker inspect` or
use registry HTTP API to fetch manifest digest.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


class DigestMismatchError(Exception):
    pass


class RepositoryMappingError(Exception):
    pass


def load_metadata(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check_repo_mapping(repository: str, is_main: bool) -> None:
    if is_main:
        if repository.endswith("-staging"):
            raise RepositoryMappingError("main branch must not deploy staging image")
    elif not repository.endswith("-staging"):
        raise RepositoryMappingError("feature branch must deploy staging image")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--metadata", required=True)
    p.add_argument("--repository", required=True)
    p.add_argument("--image-sha", required=True)
    p.add_argument("--is-main", action="store_true")
    args = p.parse_args(argv)

    meta = load_metadata(Path(args.metadata))
    recorded = meta.get("image_digest")
    if not recorded:
        print("recorded digest missing in metadata", file=sys.stderr)
        return 1
    # Stub: live digest == recorded
    live = recorded
    if live != recorded:
        print(f"digest mismatch live={live} recorded={recorded}", file=sys.stderr)
        raise DigestMismatchError("digest mismatch")
    check_repo_mapping(args.repository, args.is_main)
    print(f"deploy guard ok digest={recorded}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
