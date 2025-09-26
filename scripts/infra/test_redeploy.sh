#!/usr/bin/env bash
# Simulate a redeploy scenario producing a second endpoint artifact.
# Objective: ensure new artifact timestamp (mtime) differs and endpoint can change.
# This is a lightweight local test harness for CI (T019).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
ARTIFACT="$ROOT_DIR/infra/akash-banano/endpoint.json"
MOCK_FILE="$ROOT_DIR/infra/akash-banano/mock_ports.txt"
DISCOVER="$SCRIPT_DIR/discover_banano_endpoint.sh"
VALIDATE="$SCRIPT_DIR/validate_endpoint.py"

if [[ ! -x "$DISCOVER" ]]; then
  echo "discovery script not executable" >&2
  exit 1
fi

# Prepare first mock
cat > "$MOCK_FILE" <<EOF
7072:48001 testnet1.example.com
EOF
bash "$DISCOVER" || { echo "first discovery failed" >&2; exit 1; }
first_ep=$(jq -r '.banano_rpc_endpoint' < "$ARTIFACT")
first_time=$(stat -f %m "$ARTIFACT")

sleep 1 # ensure mtime difference

# Prepare second mock with different port
cat > "$MOCK_FILE" <<EOF
7072:48002 testnet1.example.com
EOF
bash "$DISCOVER" || { echo "second discovery failed" >&2; exit 1; }
second_ep=$(jq -r '.banano_rpc_endpoint' < "$ARTIFACT")
second_time=$(stat -f %m "$ARTIFACT")

if [[ "$first_ep" == "$second_ep" ]]; then
  echo "[redeploy-test][failure] endpoint did not change: $first_ep" >&2
  exit 1
fi
if [[ "$second_time" -le "$first_time" ]]; then
  echo "[redeploy-test][failure] artifact timestamp did not increase" >&2
  exit 1
fi

python3 "$VALIDATE" "$second_ep" >/dev/null || { echo "[redeploy-test][failure] second endpoint invalid" >&2; exit 1; }

echo "[redeploy-test][success] first=$first_ep second=$second_ep" >&2
