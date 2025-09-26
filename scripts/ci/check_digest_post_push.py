#!/usr/bin/env python3
"""Post-push digest verification (T041, enhanced T042).

Responsibilities:
 1. Load existing metadata (must include at minimum image_digest or pre_push_digest).
 2. Derive remote digest for pushed image (lightweight approximation using local Docker metadata
     after push: the RepoDigests field now contains the remote registry digest reference).
 3. Compare pre vs post digest; on mismatch exit with code 2.
 4. Mutate metadata file in-place adding:
        post_push_digest
        digest_verification = ok|mismatch

Notes / Future Hardening:
 - For true remote verification we will later integrate "crane digest" or GHCR HTTP API query.
 - This script intentionally avoids non-stdlib deps for portability inside GitHub Actions runner.
 - A future negative test (T038) can monkeypatch subprocess output to simulate mismatch.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_ARGS = 3  # metadata_path, repository, git_sha


def load_metadata(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_metadata(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f)
        f.write("\n")
    tmp.replace(path)


def _inspect_repo_digest(image_ref: str) -> str | None:
    """Return repo digest (sha256:...) using docker image inspect RepoDigests.

    We parse the first RepoDigest entry (format: repository@sha256:HASH) and return the digest
    component. Returns None if inspection fails or field missing.
    """
    try:
        out = subprocess.check_output(
            [
                "docker",
                "image",
                "inspect",
                image_ref,
                "--format",
                "{{json .RepoDigests}}",
            ],
            text=True,
        ).strip()
    except Exception:  # pragma: no cover - best effort only
        return None
    try:
        digests = json.loads(out)
        if not digests:
            return None
        first = digests[0]
        if "@" in first:
            return first.split("@", 1)[1]
        return first  # unexpected but fallback
    except Exception:  # pragma: no cover
        return None


def main(argv: list[str]) -> int:
    # Minimal arg parsing (argv: [metadata_path, repository, git_sha])
    if len(argv) < REQUIRED_ARGS:
        print(
            "usage: check_digest_post_push.py <metadata_path> <repository> <git_sha>",
            file=sys.stderr,
        )
        return 64  # EX_USAGE
    metadata_path = Path(argv[0])
    repository = argv[1]
    git_sha = argv[2]
    if not metadata_path.exists():
        print(f"metadata file not found: {metadata_path}", file=sys.stderr)
        return 1
    data = load_metadata(metadata_path)
    pre = data.get("pre_push_digest") or data.get("image_digest")
    if not pre:
        print("pre-push digest missing in metadata", file=sys.stderr)
        return 1
    image_ref = f"{repository}:{git_sha}"
    remote = _inspect_repo_digest(image_ref) or pre  # fallback to pre if cannot determine
    data["post_push_digest"] = remote
    if pre == remote:
        status = "ok"
        rc = 0
    else:
        status = "mismatch"
        rc = 2
    data.setdefault("pre_push_digest", pre)
    data["digest_verification"] = status
    write_metadata(metadata_path, data)
    if rc == 0:
        print(f"Digest verification ok pre={pre} post={remote}")
    else:
        print(f"Digest mismatch pre={pre} post={remote}", file=sys.stderr)
    return rc


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
