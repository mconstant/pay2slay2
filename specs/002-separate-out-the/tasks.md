# Tasks: Split Akash Deployments (Banano Node & API Separation)

**Input**: Design documents from `specs/002-separate-out-the/`
**Prerequisites**: plan.md (PASS), research.md, data-model.md, contracts/, quickstart.md

## Constitution Gate Verification
- Plan Constitution Check: PASS (initial + post-design)
- Security considerations present
- Decentralized topology + upgrade strategy documented
- Performance targets declared
- Observability hooks (logging requirements) identified
- All clarifications resolved (no NEEDS CLARIFICATION markers)

## Execution Rules
Ordering: Setup → Tests (fail first) → Implementation → Integration → Polish.  
Parallel `[P]` only when tasks touch different files/directories with no dependency.

## Phase 3.1: Setup
- [x] T001 Create infra directory skeleton: `infra/akash-banano/` and `infra/akash-api/` (README placeholders)  
  Files: `infra/akash-banano/README.md`, `infra/akash-api/README.md`
- [x] T002 Add Terraform scaffolding for Banano: `infra/akash-banano/main.tf`, `outputs.tf`, `variables.tf`, minimal provider + Akash deployment resource (placeholder image, internal ports 7071,7072,7074)  
  Depends: T001
- [x] T003 Add Terraform scaffolding for API: `infra/akash-api/main.tf`, `variables.tf` (includes `banano_rpc_endpoint`), `outputs.tf` (deployment_id only)  
  Depends: T001
- [x] T004 [P] Add `.github/workflows/banano-deploy.yml` skeleton with workflow_dispatch, terraform init/apply stub (no logic yet)  
  Depends: T002
- [x] T005 [P] Add `.github/workflows/api-deploy.yml` skeleton with workflow_dispatch, terraform init/apply stub referencing `infra/akash-api`  
  Depends: T003
- [x] T006 Add shared script directory `scripts/infra/` with placeholder `discover_banano_endpoint.sh` (returns non-zero unimplemented)  
  Depends: T004

## Phase 3.2: Tests First (Contract & Integration) – MUST FAIL INITIALLY
- [x] T007 [P] Expand existing `tests/contract/test_endpoint_artifact.py` to cover CT-001..CT-006 (mark xfail where not yet implemented)  
  Depends: T004 (skeleton present)  
- [x] T008 [P] Add `tests/integration/test_api_requires_endpoint.py` simulating missing artifact scenario → expect failure path (use environment var absence)  
  Depends: T005
- [x] T009 [P] Add `tests/integration/test_endpoint_validation.py` covering invalid host, invalid port, empty JSON conditions (simulate artifact parsing function to add)  
  Depends: T007

## Phase 3.3: Core Implementation (Banano Workflow)
- [x] T010 Implement `scripts/infra/ak_cmd.sh` helper (common Akash CLI wrapper; idempotent)  
  Depends: T006
- [x] T011 Implement full `discover_banano_endpoint.sh` with retry schedule (5 10 20 40) and exit behavior (no artifact on fail)  
  Depends: T010
- [x] T012 Implement Terraform Akash SDL template for Banano (e.g. `infra/akash-banano/banano.sdl.yaml`) referencing required ports  
  Depends: T002
- [x] T013 Wire Banano workflow steps: checkout → setup terraform → apply → run discovery script → validate host:port → write `infra/akash-banano/endpoint.json` → upload artifact → set GHA output  
  Depends: T011,T012
- [x] T014 Add validation script `scripts/infra/validate_endpoint.py` (Python) implementing DNS/IPv4 + port rules (used by both workflows)  
  Depends: T011

## Phase 3.4: Core Implementation (API Workflow Consumption)
- [x] T015 Implement artifact download + parse step in `api-deploy.yml` (uses `actions/download-artifact`) → export `BANANO_RPC_ENDPOINT` env var  
  Depends: T013,T014
- [x] T016 Add fail-fast step if artifact missing / parse fails / validation fails (shell + Python validator)  
  Depends: T015
- [x] T017 Inject variable into Terraform apply for API stack (`-var="banano_rpc_endpoint=$BANANO_RPC_ENDPOINT"`)  
  Depends: T016

## Phase 3.5: Integration & Observability
- [x] T018 Enhance Banano workflow logs: attempt counters, success line, failure line (FR-007)  
  Depends: T013
- [x] T019 Add redeploy scenario test script `scripts/infra/test_redeploy.sh` (simulate second artifact, ensure different timestamp)  
  Depends: T013
- [x] T020 Add doc `docs/operations/split-deployments.md` summarizing steps (operator process FR-014)  
  Depends: T017
- [x] T021 Add optional metric stub (commented) in discovery script for future Prometheus sidecar (documentation only)  
  Depends: T018

## Phase 3.6: Polish & Hardening
- [x] T022 Add tflint config & GitHub Action (deferred earlier; now implement)  
  Depends: T002,T003
- [x] T023 Add schema file `specs/002-separate-out-the/contracts/endpoint.schema.json` matching artifact spec (update tests to use it)  
  Depends: T007
- [x] T024 Refine contract tests: remove xfail once implementation present; ensure all pass  
  Depends: T013,T015,T023
- [ ] T025 Update `quickstart.md` with real command snippets for workflows & redeploy notes  
  Depends: T024
- [ ] T026 Add CHANGELOG entry describing feature  
  Depends: T025
- [ ] T027 Final Constitution re-check & tasks closure summary  
  Depends: T026

## Dependencies Summary
- Setup foundation (T001–T006) precedes tests.
- Tests (T007–T009) precede core implementation tasks referencing them.
- Banano workflow implementation (T010–T014) precedes API consumption (T015–T017).
- Observability & docs (T018–T021) follow core wiring.
- Polish (T022–T027) finalize quality gates.

## Parallel Execution Examples
Group A (post-setup):
```
T004 T005 (workflow skeletons different files)
```
Group B (tests phase):
```
T007 T008 T009
```
Group C (later polish when unblocked):
```
T022 T023 (in different directories), after their deps
```

## Validation Checklist Mapping
- Contracts → T007,T023,T024
- Entities → Represented in infra & artifact tasks (Banano Deployment, Endpoint Artifact)
- Retry/Failure semantics → T011,T013,T018
- Validation rules → T014,T016,T023
- Logging/Observability → T018,T021
- Operator docs → T020,T025
- Performance target (discovery latency) indirectly validated by log timestamps (manual) – note in docs (T020)

## Notes
- All test files created/expanded before functional implementation.
- No DB schema changes required; focus is CI/CD & infra scripts.
- Keep scripts POSIX sh compatible where feasible (bash features acceptable if needed for arrays/backoff logic).
