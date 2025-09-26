#!/usr/bin/env python3
"""Read ci/latest_build.json and print fields for use in docs or scripts.

Usage:
  python scripts/ci/read_latest_build.py --field image_sha
  python scripts/ci/read_latest_build.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_PATH = Path("ci/latest_build.json")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--file", default=str(DEFAULT_PATH))
    p.add_argument("--field", help="Specific field to print (image_sha|build_run_id)")
    p.add_argument("--all", action="store_true", help="Print entire JSON")
    args = p.parse_args(argv)
    path = Path(args.file)
    if not path.exists():
        print("latest build info not found", file=sys.stderr)
        return 1
    data = json.loads(path.read_text(encoding="utf-8"))
    if args.all:
        json.dump(data, sys.stdout)
        sys.stdout.write("\n")
        return 0
    if args.field:
        if args.field not in data:
            print(f"Field {args.field} missing", file=sys.stderr)
            return 2
        print(data[args.field])
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
