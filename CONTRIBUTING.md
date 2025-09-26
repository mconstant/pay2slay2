# Contributing Guide

Thanks for your interest in Pay2Slay.

## Development Environment
1. Python 3.11+
2. `pip install -e .[dev]`
3. Run `pre-commit install` (if configured) to auto-format & type-check.

## Workflow
- Create feature branch off latest default.
- Add or update tests before implementing user-visible changes.
- Ensure `ruff`, `mypy`, and `pytest` pass locally.
- Update `specs/001-pay2slay-faucet/tasks.md` if task completion status changes.

## Commit Messages
Use conventional style:
```
feat(component): short description (T0XX)
fix(component): bug description
chore: tooling / infra changes
```

## Pull Requests
Include:
- Problem statement
- Summary of changes
- Testing evidence (logs, screenshots, or metrics where applicable)

## Code Style
- Enforced via Ruff + auto-format.
- Prefer pure functions and explicit dataclasses for payloads.
- Keep modules cohesive; factor shared logic into `src/lib`.

## Tests
- Contract tests in `tests/contract/`
- Integration tests in `tests/integration/`
- Unit tests in `tests/unit/`
- Ensure new tests initially fail before implementation (TDD ideal).

## Documentation
Update docs in `docs/` for new endpoints or configuration fields.

## Security
Never commit secrets. Use environment variables and reference them in YAML via `${VAR}` interpolation.

## License
By contributing you agree your code is provided under the project license.
