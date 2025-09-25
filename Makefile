# Simple dev Makefile

.PHONY: api scheduler test lint type all
.PHONY: ci deploy-akash workflow-ci workflow-deploy-akash

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
	gh workflow run deploy-akash -f image_tag=$(IMAGE_TAG) -f akash_network=$(AKASH_NETWORK)

# Trigger CI workflow remotely (uses current default branch HEAD)
workflow-ci:
	@if ! command -v gh >/dev/null 2>&1; then echo 'gh CLI not installed'; exit 1; fi
	gh workflow run ci

# Trigger deploy-akash with variables (same as deploy-akash target alias for clarity)
workflow-deploy-akash: deploy-akash
