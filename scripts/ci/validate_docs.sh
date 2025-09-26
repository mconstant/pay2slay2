#!/usr/bin/env bash
set -euo pipefail
# Documentation validation script (T055)
# Ensures required themes are present in distribution & quickstart docs.

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
DIST="$ROOT_DIR/docs/distribution.md"
QS="$ROOT_DIR/docs/quickstart.md"

missing=0
check() {
  local file=$1
  local term=$2
  if ! grep -qi -- "$term" "$file"; then
    echo "[missing] '$term' not found in $file" >&2
    missing=1
  fi
}

required_dist=(
  "immutable" "digest integrity" "rollback" "short tag parity" "SBOM" "linux/amd64" "image_build_total" "rollback_total"
)
required_qs=(
  "immutable" "rollback" "digest" "image_build_total" "rollback_total"
)

for t in "${required_dist[@]}"; do check "$DIST" "$t"; done
for t in "${required_qs[@]}"; do check "$QS" "$t"; done

if [ $missing -ne 0 ]; then
  echo "Documentation validation FAILED" >&2
  exit 1
fi
echo "Documentation validation passed" >&2
