#!/usr/bin/env bash
set -euo pipefail

# ak_cmd.sh - thin wrapper for Akash CLI interactions.
# This is intentionally minimal until real CLI integration is wired.
# Usage: ./scripts/infra/ak_cmd.sh <subcommand ...>

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <akash-cli-args>" >&2
  exit 2
fi

if ! command -v akash >/dev/null 2>&1; then
  echo "[ak_cmd] akash CLI not installed in runner environment" >&2
  exit 127
fi

echo "[ak_cmd] executing: akash "$*"" >&2
exec akash "$@"
