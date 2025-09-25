# Tasks: Pay2Slay Faucet

**Input**: Design documents from `/specs/001-pay2slay-faucet/`  
**Prerequisites**: spec.md (available), plan.md (PASS), research/data-model/contracts (to be generated in Phase 1)

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → PASS Constitution Check detected
   → Structure: Option 1 (single project)
2. Load optional design documents (none present yet)
3. Generate tasks by category from spec.md requirements
4. Apply task rules (TDD-first, [P] for independent files)
5. Number tasks sequentially (T001, T002...)
6. Create parallel execution examples
7. Return: SUCCESS (tasks ready for execution)
```

## Constitution Check (pre-task generation)
PASS — plan.md includes Security, Tests (TDD), UX, Performance, Observability, Licensing/SBOM, Decentralized/Blockchain notes. No open clarifications.

## Path Conventions
- Single project (DEFAULT):
  - src/ models/, services/, api/, jobs/, lib/
  - tests/ contract/, integration/, unit/
  - configs/ payout.yaml, integrations.yaml, product.yaml (operator-edited)

---

## Phase 3.1: Setup
- [x] T001 Create project structure (single project)
      - Create directories: `src/models/`, `src/services/`, `src/api/`, `src/jobs/`, `src/lib/`, `tests/contract/`, `tests/integration/`, `tests/unit/`, `configs/`, `docs/`
      - Add placeholder `__init__` or README files to each new directory
      - Dependency: none
- [x] T002 Initialize Python project (pyproject.toml) with dependencies
      - Add: fastapi, uvicorn, pydantic, sqlalchemy, alembic, httpx, pyyaml, structlog, prometheus-client, opentelemetry-instrumentation, tenacity
      - Dev: pytest, pytest-asyncio, httpx[http2], coverage, ruff, mypy, types-PyYAML
      - Dependency: T001
- [ ] T003 [P] Configure linting/formatting/type-checking
      - Ruff config, Black via Ruff, Mypy strict, EditorConfig
      - Pre-commit hooks (ruff/mypy/pytest on staged)
      - Dependency: T002
- [x] T004 Write configs with spec defaults
      - Create `configs/payout.yaml` with: payout_amount_ban_per_kill: 2.1, scheduler_minutes: 20, daily_payout_cap: 1, weekly_payout_cap: 3, reset_tz: UTC, settlement_order: random, batch_size: 0
      - Create `configs/integrations.yaml` with: chain_env: testnet, node_rpc: "", min_operator_balance_ban: 50, dry_run: true, yunite_api_key: ${YUNITE_API_KEY}, yunite_guild_id: "", discord_guild_id: "", discord_oauth_client_id: ${DISCORD_CLIENT_ID}, discord_oauth_client_secret: ${DISCORD_CLIENT_SECRET}, discord_redirect_uri: http://localhost:3000/auth/discord/callback, oauth_scopes: [identify, guilds], fortnite_api_key: ${FORTNITE_API_KEY}, rate_limits: {fortnite_per_min: 60}, abuse_heuristics: {kill_rate_per_min: 10}
      - Create `configs/product.yaml` with: app_name: "Pay2Slay Faucet", org_name: "Example Org", banner_url: "", media_kit_url: "", default_locale: en, feature_flags: {dry_run_banner: true}
      - Dependency: T001
- [ ] T005 [P] Docs skeleton in `docs/` (README, SECURITY, CONTRIBUTING, LICENSE, QUICKSTART)
      - Include no-KYC policy and regional analytics privacy note
      - Dependency: T001

## Phase 3.2: Tests First (TDD) — MUST COMPLETE BEFORE 3.3
- [x] T006 Contract test: POST `/auth/discord/callback` → creates/updates session in `tests/contract/test_auth_callback.py`
      - Assert OAuth state validation, guild membership required, Yunite mapping required
      - Dependency: T002, T003
- [x] T007 [P] Contract test: POST `/link/wallet` in `tests/contract/test_link_wallet.py`
      - Validates Banano address; links wallet to authenticated Discord user
      - Dependency: T002, T003
- [x] T008 [P] Contract test: GET `/me/status` in `tests/contract/test_me_status.py`
      - Returns linkage status, last verification time, accrued rewards
      - Dependency: T002, T003
- [x] T009 [P] Contract test: POST `/admin/reverify` in `tests/contract/test_admin_reverify.py`
      - Admin-only; triggers re-verify; requires audit entry
      - Dependency: T002, T003
- [x] T010 [P] Contract test: POST `/admin/payouts/retry` in `tests/contract/test_admin_payouts_retry.py`
      - Admin-only; retry failed payout; idempotent on tx hash
      - Dependency: T002, T003
- [ ] T011 Integration test: registration + linking in `tests/integration/test_registration_flow.py`
      - Discord OAuth → Yunite EpicID mapping → wallet link → status
      - Dependency: T006–T008
- [ ] T012 [P] Integration test: accrual and settlement in `tests/integration/test_settlement_flow.py`
      - Simulate kill deltas; scheduler pays 2.1 BAN/kill; enforce daily/weekly caps
      - Dependency: T006–T008
- [ ] T013 [P] Performance smoke: `/me/status` p95 < 300ms in `tests/integration/test_perf_status.py`
      - Dependency: T006–T008
- [ ] T014 [P] Security tests: OAuth replay, input validation, rate limiting in `tests/integration/test_security.py`
      - Dependency: T006–T008

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T015 Config loader in `src/lib/config.py`
      - Load/validate YAMLs; env override; fail fast on missing keys
      - Dependency: T004
- [x] T016 Models in `src/models/` [P]
      - `user.py`, `wallet_link.py`, `verification_record.py`, `reward_accrual.py`, `payout.py`, `admin_user.py`
      - Dependency: T015
- [x] T017 Services I: external in `src/services/` [P]
      - `discord_auth_service.py`, `yunite_service.py`, `fortnite_service.py`
      - Dependency: T016
- [x] T018 Services II: domain in `src/services/` [P]
      - `accrual_service.py`, `settlement_service.py`, `payout_service.py`, `abuse_analytics_service.py`
      - Dependency: T016, T017
- [x] T019 API: auth/user in `src/api/auth.py`, `src/api/user.py`
      - `/auth/discord/callback`, `/me/status`, `/link/wallet`
      - Session cookie `p2s_session` issued on auth and validated in user endpoints
      - Dependency: T017, T018
- [ ] T020 [P] API: admin in `src/api/admin.py`
      - `/admin/reverify`, `/admin/payouts/retry`, `/admin/health`
      - Dependency: T018
- [ ] T021 [P] Jobs: scheduler in `src/jobs/settlement.py`
      - Interval runner; enforces `min_operator_balance_ban`; batch_size; metrics
      - Dependency: T018
- [ ] T022 Observability wiring in `src/lib/observability.py`
      - structlog setup; Prometheus metrics; tracing init
      - Dependency: T019–T021
- [ ] T023 Error handling and validation in `src/lib/http.py`
      - Error responses; validation; rate limit responses
      - Dependency: T019–T020
- [ ] T024 Secrets management wiring
      - Read secrets from env/secret store; remove plaintext
      - Dependency: T015, T017

## Phase 3.4: Integration
- [x] T025 Database setup
      - SQLAlchemy models, Alembic migrations; SQLite dev; DSN configurable
      - Dependency: T016
- [ ] T026 Auth middleware/session handling
      - Validate OAuth state, scopes; deserialize user
      - Note: cookie verified inline in endpoints; dedicated middleware still pending
      - Dependency: T019
- [ ] T027 Request/response logging and security headers
      - Correlation IDs; CORS; headers baseline
      - Dependency: T022, T023
- [ ] T028 Dependency and license scanning in CI (SBOM)
      - Add Syft/Grype or pip-licenses; generate NOTICE
      - Dependency: T002
- [ ] T029 [conditional] Artifact signing & verification
      - Sign container/images (cosign); document verification
      - Dependency: T002
- [ ] T030 Deployment artifacts for Akash
      - Compose manifests and docs; include secrets references
      - Dependency: T019–T022

## Phase 3.5: Polish
- [ ] T031 [P] Unit tests for services in `tests/unit/` (accrual, settlement, payout)
      - Dependency: T018
- [ ] T032 Performance tests in `tests/integration/test_perf_endpoints.py`
      - Verify p95 targets; load test key paths
      - Dependency: T019–T021
- [ ] T033 [P] Update API docs (`docs/api.md`) and generate OpenAPI
      - Dependency: T019–T020
- [ ] T034 [P] Manual test script `docs/quickstart.md`
      - Discord login, wallet link, accrual, settlement, admin actions
      - Dependency: T019–T021
- [ ] T035 [P] Update SECURITY.md and LICENSE/NOTICE with dependency licenses
      - Dependency: T028
- [ ] T036 [P] Document distribution/upgrade strategy `docs/distribution.md`
      - Artifact signing, Akash deployment, upgrade plan
      - Dependency: T029–T030

## Validation Checklist
- [ ] All tests present and failing before implementation (T006–T014)
- [ ] Performance tests included and targets checked (T013, T032)
- [ ] UX/accessibility checks included if UI added later
- [ ] Observability tasks added for critical flows (T022)
- [ ] Security tests and dependency/license scanning included (T014, T028)
- [ ] Decentralized distribution/signing and blockchain tasks included (T029, T030)

## Dependencies
- Setup (T001–T005) → Tests (T006–T014) → Core (T015–T024) → Integration (T025–T030) → Polish (T031–T036)
- T016 blocks T017–T018; T018 blocks T019–T021; T022 blocks T027
- Admin endpoints (T020) depend on domain services (T018)

## Parallel Example
```
# Launch contract/integration tests in parallel once setup is done:
pytest -k test_auth_callback.py        # T006
pytest -k test_link_wallet.py          # T007
pytest -k test_me_status.py            # T008
pytest -k test_admin_reverify.py       # T009
pytest -k test_admin_payouts_retry.py  # T010
pytest -k test_settlement_flow.py      # T012
pytest -k test_perf_status.py          # T013
pytest -k test_security.py             # T014
```

## Notes
- [P] tasks = different files, no dependencies
- Ensure tests fail before implementing
- Commit after each task
- Keep secrets out of repo; use env/secret store

---

Generated from spec: `/specs/001-pay2slay-faucet/spec.md` and plan: `/specs/001-pay2slay-faucet/plan.md` on 2025-09-24.
