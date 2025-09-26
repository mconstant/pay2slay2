#!/usr/bin/env python3
"""Update api-deploy workflow dispatch defaults for image_sha and build_run_id.

This rewrites (in-place) the given workflow file replacing or inserting:
  default: <SHA>
  default: <RUN_ID>
under the respective inputs.image_sha and inputs.build_run_id blocks.

Idempotent: running with the same values will yield no diff.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def replace_block(lines: list[str], key: str, new_default: str) -> list[str]:
    pattern = re.compile(rf"^(\s*){re.escape(key)}:\s*$")
    i = 0
    while i < len(lines):
        if pattern.match(lines[i]):
            indent_match = pattern.match(lines[i])
            assert indent_match
            base_indent = indent_match.group(1)
            # look ahead for existing default within this block (greater indent)
            j = i + 1
            inserted = False
            while j < len(lines):
                line = lines[j]
                # Block ends when indentation <= base_indent and line not blank
                if line.strip() and (len(line) - len(line.lstrip())) <= len(base_indent):
                    break
                if re.match(rf"^{base_indent}\s+default:\s*", line):
                    # Replace existing default line
                    lines[j] = re.sub(r"default:.*", f"default: {new_default}", line)
                    inserted = True
                    break
                j += 1
            if not inserted:
                # Insert after key line unless description line exists directly after; prefer after description
                insert_pos = i + 1
                if insert_pos < len(lines) and re.match(
                    rf"^{base_indent}\s+description:", lines[insert_pos]
                ):
                    # insert after description line
                    insert_pos += 1
                lines.insert(insert_pos, f"{base_indent}  default: {new_default}\n")
            return lines
        i += 1
    raise SystemExit(f"Did not find input key '{key}' in workflow file")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="Path to api-deploy workflow")
    ap.add_argument("--sha", required=True, help="40-char git SHA")
    ap.add_argument("--run-id", required=True, help="Build workflow run ID")
    args = ap.parse_args(argv)

    wf_path = Path(args.file)
    text = wf_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    lines = replace_block(lines, "image_sha", args.sha)
    lines = replace_block(lines, "build_run_id", args.run_id)
    new_text = "".join(lines)
    if new_text != text:
        wf_path.write_text(new_text, encoding="utf-8")
        print(f"Updated defaults: image_sha={args.sha} build_run_id={args.run_id}")
    else:
        print("Defaults already up to date")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
