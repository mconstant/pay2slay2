#!/usr/bin/env bash
set -euo pipefail

RETRIES=(5 10 20 40)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATE="$SCRIPT_DIR/validate_endpoint.py"
OUTPUT_JSON="infra/akash-banano/endpoint.json"

echo "[discover] starting Banano RPC endpoint discovery" >&2

# Placeholder discovery: in a real Akash environment we would parse provider lease info.
# For now, simulate by reading a mock file if present (developer can inject during CI).
MOCK_FILE="infra/akash-banano/mock_ports.txt"

attempt=0
found=""
for delay in "${RETRIES[@]}"; do
	attempt=$((attempt+1))
	echo "[discover] Attempt ${attempt}/${#RETRIES[@]}" >&2
	if [[ -f "$MOCK_FILE" ]]; then
		# Expect line format: internal:external host
		while read -r line; do
			[[ -z "$line" ]] && continue
			internal_port=$(echo "$line" | awk '{print $1}' | cut -d: -f1)
			external_port=$(echo "$line" | awk '{print $1}' | cut -d: -f2)
			host=$(echo "$line" | awk '{print $2}')
			if [[ "$internal_port" == "7072" && -n "$external_port" && -n "$host" ]]; then
				candidate="${host}:${external_port}"
				if python3 "$VALIDATE" "$candidate" >/dev/null 2>&1; then
					found="$candidate"
					break 2
				else
					echo "[discover] candidate failed validation: $candidate" >&2
				fi
			fi
		done <"$MOCK_FILE"
	fi
	echo "[discover] sleeping ${delay}s" >&2
	sleep "$delay"
done

if [[ -z "$found" ]]; then
	echo "[discover] failed to resolve Banano RPC endpoint after ${#RETRIES[@]} attempts" >&2
	exit 1
fi

echo "[discover] Banano RPC endpoint resolved: $found" >&2
printf '{"banano_rpc_endpoint": "%s"}\n' "$found" > "$OUTPUT_JSON"
echo "[discover] wrote $OUTPUT_JSON" >&2

