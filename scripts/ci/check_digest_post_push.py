#!/usr/bin/env python3
"""Post-push digest verification (T041, refined).

Previous version compared the local image config digest (.Id) gathered pre-push with the
registry *manifest* digest (from RepoDigests). Those two digests refer to different objects
and will never match for a normal image, causing false-negative mismatches.

Refined Responsibilities:
 1. Load existing metadata (must include at minimum image_digest or pre_push_digest).
 2. Re-inspect the image config digest (.Id) after push and assert it is unchanged from pre.
     This guards against an accidental rebuild or tag re-assignment within the workflow.
 3. Capture the registry manifest digest (RepoDigests first entry) and store it as
     post_push_digest for downstream consumers (deploy guard, provenance, etc.).
 4. Set digest_verification = "ok" if config digest stable, else "mismatch" (exit 2 on mismatch).

Notes / Future Hardening:
 - A future enhancement may store both config_digest and manifest_digest distinctly; we retain
    the legacy field names to avoid breaking existing contracts/tests.
 - True remote verification (querying registry API) can supplement this local inspection.
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
    """Return registry manifest digest (sha256:...) via RepoDigests field.

    We parse the first RepoDigest entry (format: repository@sha256:HASH) and return only the
    digest component. Returns None if inspection fails or field missing.
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


def _inspect_config_digest(image_ref: str) -> str | None:
    """Return the image config digest (.Id) for the local image reference."""
    try:
        out = subprocess.check_output(
            [
                "docker",
                "image",
                "inspect",
                image_ref,
                "--format",
                "{{.Id}}",
            ],
            text=True,
        ).strip()
        return out or None
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
    # Re-inspect config digest post-push
    current_config = _inspect_config_digest(image_ref)
    manifest_digest = _inspect_repo_digest(image_ref)  # may be None if not yet populated

    if current_config is None:
        print("Unable to re-inspect image config digest post-push", file=sys.stderr)
        return 1

    if current_config != pre:
        # True mismatch: local image mutated (unexpected rebuild or tag repointed)
        data["post_push_digest"] = manifest_digest or current_config
        data.setdefault("pre_push_digest", pre)
        data["digest_verification"] = "mismatch"
        write_metadata(metadata_path, data)
        print(
            f"Digest mismatch (config changed) pre={pre} current={current_config} manifest={manifest_digest}",
            file=sys.stderr,
        )
        return 2

    # Config digest stable; record manifest digest (may differ by design) and mark ok
    data.setdefault("pre_push_digest", pre)
    data["post_push_digest"] = manifest_digest or current_config
    data["digest_verification"] = "ok"
    write_metadata(metadata_path, data)
    print(
        f"Digest verification ok config_digest={pre} manifest_digest={manifest_digest or 'n/a'}",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
