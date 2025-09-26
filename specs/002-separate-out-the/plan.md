
# Implementation Plan: Split Akash Deployments (Banano Node & API Separation)

**Branch**: `002-separate-out-the` | **Date**: 2025-09-26 | **Spec**: `specs/002-separate-out-the/spec.md`
**Input**: Feature specification from `/specs/002-separate-out-the/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Split the existing combined Akash deployment into two independent stacks: (1) Banano node Terraform + Akash SDL and (2) API (Faucet) Terraform + Akash SDL. The Banano workflow resolves and publishes the externally forwarded RPC port (internal 7072) as a Terraform output and JSON artifact `endpoint.json`. The API workflow consumes that artifact to inject `BANANO_RPC_ENDPOINT` into its deployment, enabling independent lifecycle operations (upgrade, scale, restart) without coupling or re-deploying both services. Reliability hinges on a bounded, exponential backoff discovery of the forwarded port; failure aborts with no stale artifact. Validation enforces host/port correctness before propagation.

## Technical Context
**Language/Version**: Python 3.11 (application), Terraform ~1.8.x (infra), Akash SDL v2, GitHub Actions YAML workflows  
**Primary Dependencies**: FastAPI, SQLAlchemy, Prometheus client, Terraform Akash provider (implicit), GitHub Actions runtime, jq (workflow parsing), bash  
**Storage**: SQLite (existing app) – unchanged by this feature  
**Testing**: pytest (existing), plus new workflow contract tests (JSON schema + mock validation)  
**Target Platform**: Akash decentralized cloud (Linux containers)  
**Project Type**: single backend service repository with split infra directories  
**Performance Goals**: Endpoint discovery 95% < 45s after Terraform apply; additional workflow overhead < 60s average  
**Constraints**: No leaked bogus endpoint; retries bounded (≤ ~75s total); zero manual input needed for API workflow in default path  
**Scale/Scope**: One Banano node deployment and one API deployment per environment (no multi-environment matrix yet)  

Additional Context Resolved:
- Validation regex: host `[a-z0-9.-]+` (must contain at least one alphabetic or hyphen segment; reject empty); port numeric 1024–65535.
- Artifact schema: `{ "banano_rpc_endpoint": "<host>:<port>" }` (single key).
- Failure semantics: Hard fail with exit code 1; no artifact or workflow output produced.
- Security scope: Endpoint not secret; integrity risk acknowledged; signing deferred.
- Observability: Logged resolution line; future metric hooks possible (out-of-scope instrumentation only documented).

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Checklist Evaluation:
1. Code Quality: Existing ruff + mypy already enforced. No new language layer introduced requiring extra linter (Terraform kept minimal; optional tflint considered but deferred – documented below). PASS.
2. Test Strategy: Add contract tests validating endpoint.json against schema and simulation test that API workflow fails w/ missing artifact. Integration test can mock artifact injection into app startup env variable. PASS.
3. UX/Accessibility: Not user-facing UI; operations clarity covered (logs + artifact). PASS.
4. Performance Targets: Defined (discovery 95% < 45s, overhead < 60s). PASS.
5. Observability: Log line for resolved endpoint; failure logs cause+attempt counts; optional future metric documented. PASS.
6. AI Autonomy Guardrails: All required clarifications resolved; no hidden mutable global state; failure semantics explicit. PASS.
7. Security: Threat model & mitigations documented; no secrets added. PASS.
8. License / Dependencies: No new runtime Python dependency; workflows rely on core tools. PASS.
9. Decentralized/Blockchain: Separation of node (off-chain infra) vs. application; upgrade strategy documented; signing deferred with rationale. PASS.
10. Gas/On-chain Impact: None (infra only). PASS.

Initial Constitution Check Result: PASS (no violations requiring Complexity Tracking entry).

Post-Design Constitution Check: Re-run after producing research, data model, contracts, quickstart. No new risks introduced; size of change remains infra-scoped. PASS.

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 1 (single backend) retained; add new infra subdirectories:
```
infra/
   akash-banano/   # Terraform + SDL for Banano node
   akash-api/      # Terraform + SDL for API (accepts banano_rpc_endpoint var)
```

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md (produced – clarifications already resolved; includes decisions & alternatives)

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/endpoint.schema.json, /contracts/workflow-contract.md, failing contract test placeholders (future), quickstart.md, updated agent context file (script invocation deferred to execution step)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 18-24 numbered, ordered tasks in tasks.md (infra scope smaller than typical app feature)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | n/a | n/a |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented
- [x] AI autonomy guardrails evaluated (no silent skips)

---
*Based on Constitution v2.4.0 - See `/memory/constitution.md`*
