# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e '.[dev]'

COPY src ./src
COPY configs ./configs

EXPOSE 8000

CMD ["uvicorn", "src.api.app:create_app", "--host", "0.0.0.0", "--port", "8000"]
