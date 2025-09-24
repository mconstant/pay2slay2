# Implementation Plan: Pay2Slay Faucet

**Branch**: `001-pay2slay-faucet` | **Date**: 2025-09-24 | **Spec**: `/specs/001-pay2slay-faucet/spec.md`
**Input**: Feature specification from `/specs/001-pay2slay-faucet/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (single project)
   → Set Structure Decision accordingly
3. Fill the Constitution Check section based on the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md (outline unknowns & decisions)
6. Execute Phase 1 → contracts, data-model.md, quickstart.md (skeletons)
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

## Summary
Build an open-source, whitelabel crypto faucet that pays Banano (BAN) to Fortnite players based on verified kills. Identity is proven via Discord + Yunite (Discord→EpicID mapping). Rewards accrue per kill and are settled on a configurable interval in random user order, honoring daily/weekly caps. Operators configure three YAML files (payout, integrations, product). Deployment targets Akash Network with artifact signing and documented upgrade path.

## Technical Context
- Language/Version: Python 3.11
- Primary Dependencies: FastAPI, Pydantic, SQLAlchemy, Alembic, httpx, PyYAML, structlog, prometheus-client, OpenTelemetry instrumentation, tenacity (retries)
- Storage: SQLAlchemy ORM; SQLite for dev; configurable DSN for prod
- Testing: pytest, pytest-asyncio, coverage; TDD-first
- Target Platform: Linux containers; deploy to Akash Network
- Project Type: single project (backend API + scheduler; UI out of scope for v1 plan)
- Performance Goals:
  - API p95 latency < 300ms for linkage/status endpoints
  - Verification ≥ 50 users/minute at p95 < 2s per verification batch
  - Payout executor throughput ≥ 10 payouts/minute; idempotent, with retries
  - Node resource budget: Banano node < 512MB RAM, < 1 vCPU average
- Constraints:
  - No KYC; privacy-preserving regional analytics only
  - Operator wallet floor default 50 BAN before settlements execute
  - Daily cap 1, weekly cap 3, resets at UTC boundaries
- Scale/Scope: Initial cohort up to low tens of thousands of users; single-region deployment; horizontal scale considered later

## Constitution Check
PASS — The plan satisfies constitutional gates:
- Code Quality: Ruff, Mypy (strict), Black via Ruff; pre-commit hooks
- Test Strategy: Contract + integration tests defined before implementation; unit tests for services; performance smoke tests
- UX/Accessibility: User-facing linkage/status endpoints include acceptance criteria in spec; future UI to honor AA contrast and keyboard nav
- Performance: Targets declared above; tests planned to validate p95
- Observability: Structured logs (structlog), Prometheus metrics, OpenTelemetry tracing for auth, verification, settlement, payout flows
- Security: Threat model addressed in spec; OAuth hardening (state, redirect validation), secrets from env/secret store; audit trail for payouts
- Licensing: Dependency manifest and SBOM checks in CI; NOTICE generation
- Decentralized Distribution: Akash deployment artifacts; artifact signing (cosign); documented upgrade strategy
- Blockchain Use: Off-chain verification; on-chain payouts via Banano node; zero-fee consideration and node resource constraints; no smart contracts (security review of payout module only)

## Project Structure

### Documentation (this feature)
```
specs/001-pay2slay-faucet/
├── plan.md          # This file
├── research.md      # Phase 0 output (to be created)
├── data-model.md    # Phase 1 output (to be created)
├── quickstart.md    # Phase 1 output (to be created)
├── contracts/       # Phase 1 output (to be created)
└── tasks.md         # Phase 2 output (/tasks)
```

### Source Code (repository root) — Option 1: Single project (DEFAULT)
```
src/
├── models/
├── services/
├── api/
├── jobs/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

configs/
├── payout.yaml
├── integrations.yaml
└── product.yaml
```

**Structure Decision**: Option 1 (single project). Rationale: smallest viable surface to ship API + scheduler; UI can be a separate follow-up.

## Phase 0: Outline & Research
- Unknowns/Decisions to capture in `research.md`:
  - Fortnite API kill data best endpoint(s) and rate limits; pagination and anti-abuse nuances
  - Yunite API patterns and Discord guild membership validation specifics
  - Banano node access (RPC availability, sync behavior) and Pippen compatibility; dry-run strategy
  - Artifact signing workflow on Akash; secrets injection patterns
  - Privacy approach for regional analytics (coarse geolocation; retention; opt-out)
- Outputs: Decisions with rationale and alternatives; risks and mitigations

## Phase 1: Design & Contracts
- `data-model.md`: Entities from spec (User, WalletLink, VerificationRecord, RewardAccrual, Payout, AdminUser) with fields and relationships
- `contracts/`: REST endpoints for auth, linking, status, admin actions; OpenAPI schema
- Contract tests: one per endpoint; schema assertions and auth constraints
- `quickstart.md`: Step-by-step operator and user flow incl. Discord login → wallet link → accrual → settlement → admin

## Phase 2: Task Planning Approach
- Strategy: Generate tasks from contracts, data-model, and quickstart; tests before implementation; mark [P] for independent files
- Estimated Output: 30–40 tasks across setup, tests, core, integration, polish

## Phase 3+: Future Implementation
- Phase 3: /tasks command creates tasks.md
- Phase 4: Implement per tasks.md with TDD
- Phase 5: Validate via tests and quickstart

## Complexity Tracking
None at this time.

## Progress Tracking
**Phase Status**:
- [x] Phase 0: Research outlined
- [x] Phase 1: Design targets outlined
- [x] Phase 2: Task planning approach documented
- [ ] Phase 3: Tasks generated (/tasks)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS (no new violations introduced)
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented
