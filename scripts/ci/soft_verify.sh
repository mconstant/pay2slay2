#!/usr/bin/env bash
# Soft signature verification stub (T019)
# Behavior:
#  - If COSIGN_EXPERIMENTAL or cosign binary not present -> output unverified/missing
#  - Otherwise attempts a fake verification (placeholder) and returns verified
# Output: JSON to stdout and also key=value lines for GitHub Actions consumption when --gha flag used.

set -euo pipefail
MODE="auto"
GHA=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --gha) GHA=1; shift ;;
    --image) IMAGE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

STATUS="unverified"
REASON="missing"
if command -v cosign >/dev/null 2>&1; then
  # Placeholder: we don't actually verify; future integration point
  STATUS="unverified"
  REASON="no_signature"
fi
JSON="{\"signature_status\":\"$STATUS\",\"signature_reason\":\"$REASON\"}"
echo "$JSON"
if [[ $GHA -eq 1 ]]; then
  echo "signature_status=$STATUS" >> "$GITHUB_OUTPUT"
  echo "signature_reason=$REASON" >> "$GITHUB_OUTPUT"
fi
