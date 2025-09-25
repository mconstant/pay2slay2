# Simple dev Makefile

.PHONY: api scheduler test lint type all

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
