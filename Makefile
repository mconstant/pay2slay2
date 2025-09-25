# Simple dev Makefile

.PHONY: api scheduler test lint type all
.PHONY: ci deploy-akash workflow-ci workflow-deploy-akash rotate-akash-cert

api:
	uvicorn src.api.app:create_app --reload --port 8000

scheduler:
	python -m src.jobs

test:
	PYTHONPATH=. pytest -q

lint:
	ruff check .

type:
	mypy

all: lint type test

ci:
	python -m pip install --upgrade pip
	python -m pip install -e '.[dev]'
	ruff check .
	mypy
	PYTHONPATH=. pytest -q
	@if command -v syft >/dev/null 2>&1; then echo 'Generating SBOM (syft)'; syft . -o spdx-json > sbom.spdx.json || true; else echo 'syft not installed; skipping SBOM'; fi
	@if command -v grype >/dev/null 2>&1; then echo 'Running vulnerability scan (grype)'; grype . --fail-on high || true; else echo 'grype not installed; skipping scan'; fi

deploy-akash:
	@if ! command -v gh >/dev/null 2>&1; then echo 'gh CLI not installed'; exit 1; fi
	@if [ -z "$(IMAGE_TAG)" ]; then echo 'IMAGE_TAG required (ex: IMAGE_TAG=latest)'; exit 1; fi
	@if [ -z "$(AKASH_NETWORK)" ]; then echo 'AKASH_NETWORK required (ex: https://rpc.akash.network:443)'; exit 1; fi
	# Auto-detect current branch if REF not provided (handles detached HEAD by leaving blank)
	REF_DETECTED=$$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo ""); \
	REF_TO_USE="$(REF)"; \
	if [ -z "$$REF_TO_USE" ] && [ "$$REF_DETECTED" != "HEAD" ]; then REF_TO_USE="$$REF_DETECTED"; fi; \
	if [ -n "$$REF_TO_USE" ]; then echo "Using ref: $$REF_TO_USE"; REF_FLAG="-r $$REF_TO_USE"; else echo 'No ref provided/detected (will use default branch)'; REF_FLAG=""; fi; \
	gh workflow run deploy-akash $$REF_FLAG -f image_tag=$(IMAGE_TAG) -f akash_network=$(AKASH_NETWORK)

# Trigger CI workflow remotely (uses current default branch HEAD)
workflow-ci:
	@if ! command -v gh >/dev/null 2>&1; then echo 'gh CLI not installed'; exit 1; fi
	gh workflow run ci

# Trigger deploy-akash with variables (same as deploy-akash target alias for clarity)
workflow-deploy-akash: deploy-akash

# Rotate Akash certificate via workflow-dispatch
rotate-akash-cert:
	@if ! command -v gh >/dev/null 2>&1; then echo 'gh CLI not installed'; exit 1; fi
	KEY_NAME_ARG="deployer"; if [ -n "$(KEY_NAME)" ]; then KEY_NAME_ARG="$(KEY_NAME)"; fi; \
	METHOD_ARG="cert-generation"; if [ -n "$(ROTATE_METHOD)" ]; then METHOD_ARG="$(ROTATE_METHOD)"; fi; \
	AKASH_NET_ARG="https://rpc.akash.network:443"; if [ -n "$(AKASH_NETWORK)" ]; then AKASH_NET_ARG="$(AKASH_NETWORK)"; fi; \
	CHAIN_ID_ARG="akashnet-2"; if [ -n "$(AKASH_CHAIN_ID)" ]; then CHAIN_ID_ARG="$(AKASH_CHAIN_ID)"; fi; \
	# Auto-detect current branch if REF not provided (handles detached HEAD by leaving blank)
	REF_DETECTED=$$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo ""); \
	REF_TO_USE="$(REF)"; \
	if [ -z "$$REF_TO_USE" ] && [ "$$REF_DETECTED" != "HEAD" ]; then REF_TO_USE="$$REF_DETECTED"; fi; \
	if [ -n "$$REF_TO_USE" ]; then echo "Using ref: $$REF_TO_USE"; REF_FLAG="-r $$REF_TO_USE"; else echo 'No ref provided/detected (will use default branch)'; REF_FLAG=""; fi; \
	echo "Dispatching rotate-akash-cert ($$REF_FLAG key=$$KEY_NAME_ARG method=$$METHOD_ARG network=$$AKASH_NET_ARG chain=$$CHAIN_ID_ARG)"; \
	gh workflow run rotate-akash-cert $$REF_FLAG -f key_name=$$KEY_NAME_ARG -f rotate_method=$$METHOD_ARG -f akash_network=$$AKASH_NET_ARG -f chain_id=$$CHAIN_ID_ARG
