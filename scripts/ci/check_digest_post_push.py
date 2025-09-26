#!/usr/bin/env python3
"""Post-push digest verification (T041, initial stub).

Loads metadata.json (if present) for pre_push_digest, compares with a simulated registry digest.
In real implementation, would query registry (e.g., crane/ghcr API) for the pushed tag digest.
Currently compares against the same value so tests can later adjust to assert equality, and we
will introduce mismatch simulation in future negative test expansions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_metadata(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str]) -> int:
    metadata_path = Path(argv[0] if argv else "metadata.json")
    if not metadata_path.exists():
        print(f"metadata file not found: {metadata_path}", file=sys.stderr)
        return 1
    data = load_metadata(metadata_path)
    pre = data.get("pre_push_digest") or data.get("image_digest")
    # Placeholder: use pre as remote for now
    remote = pre
    if pre != remote:
        print(f"Digest mismatch pre={pre} remote={remote}", file=sys.stderr)
        return 2
    print(f"Digest verification ok {pre}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
