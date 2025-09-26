#!/usr/bin/env python3
"""Resolve the GitHub Actions workflow run ID for a given image (git) SHA.

Usage (local or in CI):
  python scripts/ci/resolve_build_run_id.py --sha <40-hex> [--workflow "API Build"] [--owner mconstant --repo pay2slay2]

If --owner/--repo are omitted the script attempts to derive them from the
GITHUB_REPOSITORY env var (format: owner/repo). The GitHub token is taken from
$GITHUB_TOKEN by default (override with --token-env NAME to point at a different
environment variable).

Output:
    Prints the numeric run ID to stdout on success. Exits non-zero if not found.

Typical deployment helper:
  BUILD_RUN_ID=$(python scripts/ci/resolve_build_run_id.py --sha "$SHA")
  gh workflow run 'API Deploy' -f image_sha=$SHA -f build_run_id=$BUILD_RUN_ID

Rationale:
  The deploy workflow now requires the originating build workflow run ID in
  order to deterministically fetch uniquely named artifacts (image-metadata-<SHA>).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

API_ROOT = "https://api.github.com"
DEFAULT_WORKFLOW_NAME = "API Build"
SHA_LENGTH = 40  # canonical full git SHA length


def _http_get(url: str, token: str | None) -> Any:
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
            data = resp.read()
            return json.loads(data)
    except urllib.error.HTTPError as e:  # pragma: no cover - network edge
        sys.stderr.write(f"HTTP {e.code} for {url}: {e.read().decode(errors='ignore')}\n")
        raise


def _parse_repo(owner: str | None, repo: str | None) -> tuple[str, str]:
    if owner and repo:
        return owner, repo
    env = os.getenv("GITHUB_REPOSITORY")
    if env and "/" in env:
        o, r = env.split("/", 1)
        return o, r
    raise SystemExit("Owner/repo not provided and GITHUB_REPOSITORY unset")


def find_workflow_id(owner: str, repo: str, name: str, token: str | None) -> int | None:
    # List workflows and match by name (exact)
    url = f"{API_ROOT}/repos/{owner}/{repo}/actions/workflows?per_page=100"
    data = _http_get(url, token)
    for wf in data.get("workflows", []):
        if wf.get("name") == name:
            return wf.get("id")
    return None


def find_run_id_for_sha(
    owner: str, repo: str, workflow_id: int, sha: str, token: str | None
) -> int | None:
    # Iterate pages (up to 5 * 100 runs = 500 recent runs) to find head_sha match
    for page in range(1, 6):
        url = f"{API_ROOT}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs?per_page=100&page={page}"
        data = _http_get(url, token)
        for run in data.get("workflow_runs", []):
            if run.get("head_sha") == sha:
                return run.get("id")
        if not data.get("workflow_runs"):
            break  # no more pages
    return None


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sha", required=True, help="40-char git SHA (image tag)")
    p.add_argument(
        "--workflow", default=DEFAULT_WORKFLOW_NAME, help="Workflow name (default: API Build)"
    )
    p.add_argument("--owner", help="Repository owner (fallback: GITHUB_REPOSITORY)")
    p.add_argument("--repo", help="Repository name (fallback: GITHUB_REPOSITORY)")
    p.add_argument(
        "--token-env", default="GITHUB_TOKEN", help="Name of env var holding GitHub token"
    )
    args = p.parse_args(argv)

    sha = args.sha.strip()
    if len(sha) != SHA_LENGTH or any(c not in "0123456789abcdef" for c in sha):
        sys.stderr.write("Provided --sha must be 40 lowercase hex characters\n")
        return 1

    owner, repo = _parse_repo(args.owner, args.repo)
    token = os.getenv(args.token_env)
    if not token:
        sys.stderr.write(
            f"Warning: token env '{args.token_env}' not set; may hit rate limits or fail for private repo\n"
        )

    wf_id = find_workflow_id(owner, repo, args.workflow, token)
    if wf_id is None:
        sys.stderr.write(f"Workflow named '{args.workflow}' not found in {owner}/{repo}\n")
        return 2

    run_id = find_run_id_for_sha(owner, repo, wf_id, sha, token)
    if run_id is None:
        sys.stderr.write(
            f"No run found for sha {sha} in workflow '{args.workflow}' (searched recent pages)\n"
        )
        return 3

    print(run_id)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
