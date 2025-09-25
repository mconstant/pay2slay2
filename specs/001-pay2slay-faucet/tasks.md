# Tasks: Pay2Slay Faucet

Input Sources:
- plan.md (PASS Constitution Check)
- spec.md (functional requirements & user scenarios)
- Missing currently: research.md, data-model.md, contracts/, quickstart.md (will be generated later)

Prerequisite Script Output:
```
FEATURE_DIR=/Users/mconstant/src/pay2slay2/specs/001-pay2slay-faucet
AVAILABLE_DOCS=[]
```

Generation Notes:
- Entities & endpoints inferred from spec and existing code.
- New tasks added for missing FRs (reverify endpoint, product config, payout history, region analytics, audit trail, tracing, rate limiting, Banano RPC, Fortnite deltas).
- TDD preserved: all new tests appear before related implementation tasks.

Legend: [ ] pending, [x] done, [~] partial/stub.

## Phase 3.1: Setup
- [x] T001 Project structure
- [x] T002 Dependencies
- [x] T003 Lint/format/type tooling
- [x] T004 Config YAML defaults
- [ ] T005 Docs skeleton (docs/README.md, SECURITY.md, CONTRIBUTING.md, LICENSE, QUICKSTART placeholder)

## Phase 3.2: Tests First (Contract / Integration / Perf / Security)
- [x] T006 Contract: POST /auth/discord/callback
- [x] T007 Contract: POST /link/wallet
- [x] T008 Contract: GET /me/status
- [x] T009 Contract: POST /admin/reverify
- [x] T010 Contract: POST /admin/payouts/retry
- [~] T011 Integration: registration flow (OAuth→Yunite→wallet link→status) (test added)
- [~] T012 Integration: accrual→settlement→payout (dry_run) (test added)
- [ ] T013 Performance smoke: /me/status p95<300ms
- [~] T014 Security: OAuth replay/state (state enforced), rate limit baseline, invalid wallet format fuzz
- [x] T015 Contract: POST /me/reverify (stub test created)
- [x] T016 Contract: GET /config/product (stub test created)
- [x] T017 Contract: GET /me/payouts (stub test created)

## Phase 3.3: Core Implementation
- [x] T018 Config loader (src/lib/config.py)
- [x] T019 ORM models initial (src/models/models.py)
- [x] T020 External service stubs (discord, yunite, fortnite, banano)
- [x] T021 Domain services (settlement, payout, accrual) initial
- [~] T022 Admin API (needs audit trail & health expansion)
- [x] T023 Auth/User APIs
- [~] T024 Scheduler job (needs operator balance + tracing) - accrual+settlement alternating loop implemented; tracing & real balance validation TODO
- [x] T025 OAuth state/nonce validation (basic HMAC state issued + validated)
- [x] T026 Implement /me/reverify endpoint (returns accepted + creates VerificationRecord)
- [x] T027 Implement /config/product endpoint (src/api/config.py)
- [x] T028 Implement /me/payouts endpoint (paginated)
- [~] T029 Region analytics middleware (header-based region capture; pending GeoIP + metrics)
- [ ] T030 AdminAudit model + migration + persistence utilities
- [ ] T031 Verification refresh background job (src/jobs/verification_refresh.py)
- [~] T032 FortniteService real kill delta retrieval + rate limiting
	- DONE: HTTP client (httpx), token-bucket rate limiting, dry_run path, delta computation from lifetime kills
	- DONE: Retries with jittered exponential backoff; metrics counters & latency histogram
	- DONE: Auth header configurability (header name + scheme)
	- DONE: Configurable base_url via integrations.fortnite_base_url
	- TODO: Request signing / authentication refinement if upstream requires additional headers
	- TODO: Persist observed (unsettled) kill cursor separately if needed for reconciliation
	- DONE: Integration test covering positive delta + rate limit exhaustion fallback (test_fortnite_rate_limit.py)
- [x] T033 Accrual batch job (src/jobs/accrual.py) iterating verified users (implemented + unit test)
- [ ] T034 BananoClient real RPC (balance/send/raw conversion)
- [ ] T035 Payout idempotency key (hash unsettled accrual IDs) & duplicate guard
- [ ] T036 Payout retry logic (attempt_count, last_attempt_at) + exponential backoff placeholder

## Phase 3.4: Integration & Observability
- [~] T037 Tracing setup (OpenTelemetry) in src/lib/observability.py (console + optional OTLP exporter; added span attrs in scheduler & accrual; pending: HTTP span enrichment, DB spans, metrics correlation)
- [x] T038 Correlation & trace ID logging middleware (src/lib/http.py)
- [x] T039 Rate limiting middleware (src/lib/ratelimit.py) using in-memory token bucket (extensible)
- [ ] T040 Abuse heuristic service (enrich accrual / flag abnormal kill rates)
- [ ] T041 Metrics: payouts_by_region, kills_by_region, flagged_users_total
- [ ] T042 Operator balance check (real BananoClient) integrated into scheduler
- [ ] T043 Alembic migration for AdminAudit and any new analytics columns
- [ ] T044 Secrets handling review + docs update (no plaintext, env var mapping)

## Phase 3.5: Docs & Polish
- [ ] T045 quickstart.md (operator deploy + Akash + migrations + signing)
- [ ] T046 research.md (Fortnite endpoints, Yunite specifics, Banano node, signing)
- [ ] T047 data-model.md (including cursor, audit, region, abuse fields)
- [ ] T048 contracts/ OpenAPI snapshot + per-endpoint markdown
- [ ] T049 SECURITY.md expand (OAuth state, abuse heuristics, regional privacy)
- [ ] T050 distribution/upgrade strategy (docs/distribution.md) incl. cosign & rollback
- [ ] T051 Perf harness (parallel simulated users for accrual/settlement throughput)
- [ ] T052 Decimal monetary types refactor (models/services/tests)
- [ ] T053 i18n scaffolding (src/lib/i18n.py + locale negotiation)
- [ ] T054 abuse.md documenting heuristics and flags semantics

## Phase 3.6: Security & Compliance
- [ ] T055 Expand security tests (state mismatch, replay, rate limit exhaustion)
- [ ] T056 /admin/audit query endpoint (admin_audit.py) with filters & pagination
- [ ] T057 CI SBOM gating (fail on critical vulns; attach SBOM artifact)
- [ ] T058 Cosign image signing & provenance in deploy workflow

## Phase 3.7: Advanced / Optional Enhancements
- [ ] T059 Pagination & filtering for payouts & accruals endpoints
- [ ] T060 Admin dashboard aggregation endpoint (stats & metrics)
- [ ] T061 Adaptive retry/backoff for payouts (exponential with jitter) + metric histogram
- [ ] T062 Concurrency controls & adaptive rate limiting for kill ingestion (Fortnite)

## Validation Checklist
- All contract & integration tests (T006–T017) exist before implementing corresponding features
- Accrual & settlement integration test (T012) passes before production deploy
- Performance targets verified (T013, T051)
- OAuth state enforced only after tests (T014) baseline
- Observability (T037–T041) in place prior to performance hardening
- Blockchain & distribution tasks (T050, T058) complete before public release

## Dependencies Summary
Setup → Tests → Core Services → Endpoints → Jobs → Observability/Security → Docs → Advanced
- T032 before T033
- T034 before T042 & payout idempotency tests
- T030 before T056
- T025 + T014 before enabling strict OAuth state enforcement
- T035 before scaling retries (T061)

## Parallel Execution Examples
Early contract test batch:
```
T007, T008, T009, T010, T015, T016, T017
```
Core build parallel set (post tests):
```
T030 (AdminAudit model), T032 (Fortnite real), T034 (Banano RPC), T029 (Region middleware)
```
Observability batch:
```
T037, T038, T039, T041
```

## Notes
- Distinct file tasks may run in parallel; avoid parallel edits to same module.
- Ensure each new test initially fails (capture failing assertion screenshot/log in CI if needed).
- Switch to Decimal (T052) before real money flows leave dry_run.
- Provide migration safety: run Alembic upgrade in entrypoint before app start.

Generated on 2025-09-25 (automated per tasks.prompt).
