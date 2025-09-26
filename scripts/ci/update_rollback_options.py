#!/usr/bin/env python3
"""Maintain last N build SHAs as options in the api-rollback workflow.

Strategy:
  - Insert or replace the 'options:' list under inputs.target_sha.
  - Preserve any existing non-placeholder SHAs (treat as current history) then
    append the new SHA at the top (deduplicated) and truncate to N.
  - Works idempotently if SHA already present at top.

Trigger: End of successful canonical (main/master) build.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PLACEHOLDER_PREFIX = "PLACEHOLDER_ROLLBACK_SHA_"
HISTORY_LEN = 20


def parse_options(lines: list[str], start_index: int) -> tuple[list[str], int]:
    opts: list[str] = []
    i = start_index
    indent = None
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if indent is None:
            indent = len(line) - len(line.lstrip())
        current_indent = len(line) - len(line.lstrip())
        if current_indent < indent:
            break
        if re.match(r"^\s*-\s+[0-9a-f]{40}\s*$", line):
            opts.append(line.strip().lstrip("- "))
        i += 1
    return opts, i


def update_workflow(path: Path, new_sha: str) -> bool:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if re.match(r"^\s*target_sha:\s*$", line):
            # search for options: block
            j = idx + 1
            options_line = None
            while j < len(lines) and (len(lines[j]) - len(lines[j].lstrip())) > (
                len(line) - len(line.lstrip())
            ):
                if re.match(r"^\s*options:\s*$", lines[j]):
                    options_line = j
                    break
                j += 1
            if options_line is None:
                # Insert options block after existing lines for target_sha block
                insert_at = j
                base_indent = " " * ((len(line) - len(line.lstrip())) + 2)
                new_block = [f"{base_indent}options:\n"]
                new_block.extend([f"{base_indent}- {new_sha}\n"])
                lines[insert_at:insert_at] = new_block
                path.write_text("".join(lines), encoding="utf-8")
                return True
            # parse existing options
            existing_opts, end_idx = parse_options(lines, options_line + 1)
            # Filter out placeholders
            existing_opts = [
                o for o in existing_opts if not o.startswith(PLACEHOLDER_PREFIX.lower())
            ]
            # Deduplicate preserving order
            new_list = [new_sha]
            for o in existing_opts:
                if o != new_sha and re.fullmatch(r"[0-9a-f]{40}", o):
                    new_list.append(o)
                if len(new_list) >= HISTORY_LEN:
                    break
            # Reconstruct block
            base_indent = " " * (len(lines[options_line]) - len(lines[options_line].lstrip()) + 2)
            rebuilt = [lines[options_line]] + [f"{base_indent}- {sha}\n" for sha in new_list]
            lines[options_line:end_idx] = rebuilt
            path.write_text("".join(lines), encoding="utf-8")
            return True
    raise SystemExit("target_sha input not found in workflow file")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--sha", required=True)
    args = ap.parse_args(argv)
    if not re.fullmatch(r"[0-9a-f]{40}", args.sha):
        raise SystemExit("--sha must be 40 lowercase hex")
    changed = update_workflow(Path(args.file), args.sha)
    if changed:
        print(f"Updated rollback options with {args.sha}")
    else:
        print("No changes made")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
