#!/usr/bin/env bash
# Update the Cloudflare Worker's ORIGIN_HOST secret to point to a new Akash backend.
# Usage: update_cf_origin.sh <new-akash-hostname>
# Requires: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID env vars
set -euo pipefail

NEW_ORIGIN="${1:?Usage: update_cf_origin.sh <akash-hostname>}"
WORKER_NAME="pay2slay-proxy"

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  echo "::warning::CLOUDFLARE_API_TOKEN not set — skipping origin update"
  exit 0
fi
if [ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]; then
  echo "::warning::CLOUDFLARE_ACCOUNT_ID not set — skipping origin update"
  exit 0
fi

echo "Updating Worker '${WORKER_NAME}' ORIGIN_HOST → ${NEW_ORIGIN}"

# Cloudflare API: PUT secret on a Worker
RESP=$(curl -sf -X PUT \
  "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers/scripts/${WORKER_NAME}/secrets" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"ORIGIN_HOST\",\"text\":\"${NEW_ORIGIN}\",\"type\":\"secret_text\"}" 2>&1) || {
    echo "::error::Failed to update CF Worker secret: ${RESP}"
    exit 1
  }

echo "Worker origin updated to: ${NEW_ORIGIN}"
