# pay2slay2 Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-26

## Active Technologies
- Python 3.13 (project baseline) + FastAPI, SQLAlchemy, Alembic, httpx, OpenTelemetry, Cosign (workflow tool), Docker BuildKi (003-tag-api-container)
- Python 3.13 (from project baseline) + FastAPI, SQLAlchemy, Alembic, httpx, OpenTelemetry, pytes (005-we-need-a)
- SQLite (pay2slay.db existing), PostgreSQL (for production-like testing) (005-we-need-a)

## Project Structure
```
src/
tests/
```

## Commands
cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style
Python 3.13 (project baseline): Follow standard conventions

## Recent Changes
- 005-we-need-a: Added Python 3.13 (from project baseline) + FastAPI, SQLAlchemy, Alembic, httpx, OpenTelemetry, pytes
- 003-tag-api-container: Added Python 3.13 (project baseline) + FastAPI, SQLAlchemy, Alembic, httpx, OpenTelemetry, Cosign (workflow tool), Docker BuildKi

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
