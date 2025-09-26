#!/usr/bin/env bash
set -euo pipefail

RETRIES=(5 10 20 40)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATE="$SCRIPT_DIR/validate_endpoint.py"
OUTPUT_JSON="infra/akash-banano/endpoint.json"

start_time=$(date +%s)
echo "[discover] starting Banano RPC endpoint discovery" >&2

# Placeholder discovery: in a real Akash environment we would parse provider lease info.
# For now, simulate by reading a mock file if present (developer can inject during CI).
MOCK_FILE="infra/akash-banano/mock_ports.txt"

attempt=0
found=""
for delay in "${RETRIES[@]}"; do
	attempt=$((attempt+1))
	echo "[discover][attempt] n=${attempt} of=${#RETRIES[@]} delay_next=${delay}s" >&2
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
					echo "[discover][candidate-invalid] value=$candidate" >&2
				fi
			fi
		done <"$MOCK_FILE"
	fi
	if [[ -n "$found" ]]; then
		break
	fi
	# Only sleep if not last attempt
	if [[ $attempt -lt ${#RETRIES[@]} ]]; then
		echo "[discover][sleep] seconds=${delay}" >&2
		sleep "$delay"
	fi
done

end_time=$(date +%s)
elapsed=$(( end_time - start_time ))

if [[ -z "$found" ]]; then
	echo "[discover][failure] attempts=${attempt} elapsed_s=${elapsed} message=unresolved" >&2
	# Optional future metric emission (prometheus sidecar scrape):
	# echo "banano_endpoint_discovery_success{service=\"banano\"} 0" > "${SCRIPT_DIR}/../.metrics/banano_endpoint.prom" 2>/dev/null || true
	exit 1
fi

echo "[discover][success] endpoint=$found attempts=${attempt} elapsed_s=${elapsed}" >&2
printf '{"banano_rpc_endpoint": "%s"}\n' "$found" > "$OUTPUT_JSON"
echo "[discover] wrote $OUTPUT_JSON" >&2

# Optional metric stub (T021): create directory then write gauge file (commented out for now)
# METRIC_DIR="${SCRIPT_DIR}/../.metrics"
# mkdir -p "$METRIC_DIR"
# echo "banano_endpoint_discovery_success{service=\"banano\"} 1" > "$METRIC_DIR/banano_endpoint.prom"


