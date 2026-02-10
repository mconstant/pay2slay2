# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gcc build-essential && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e .

COPY src ./src
COPY configs ./configs
COPY static ./static
COPY alembic ./alembic
COPY alembic.ini ./
COPY docker-entrypoint.sh ./

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
