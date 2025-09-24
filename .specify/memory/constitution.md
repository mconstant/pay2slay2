# pay2slay2 Constitution

<!--
Sync Impact Report
- Version change: 2.2.0 -> 2.3.0
- Modified principles: expanded to include Security & Privacy, Decentralized Distribution & Interoperability,
  Blockchain & Smart Contract Safety, Open Source Ethos & Licensing (in addition to existing quality/testing/observability guidance)
- Added sections: Security Considerations, Decentralized Distribution guidance, Licensing & Community Governance notes
- Templates updated:
  - .specify/templates/plan-template.md ✅ updated
  - .specify/templates/spec-template.md ✅ updated
  - .specify/templates/tasks-template.md ✅ updated
- Follow-up TODOs: none
-->

## Core Principles

### I. Secure Development & Privacy
Security and privacy are first-class requirements. All code and designs MUST include threat modeling, data classification, and explicit handling of sensitive data. Secrets MUST not be checked into source control. New dependencies that introduce native code, network endpoints, or cryptographic functionality MUST be reviewed and approved. Security testing (static analysis, dependency vulnerability scanning, and targeted security tests) MUST be included in the CI pipeline.

Rationale: Treating security and privacy as explicit, testable requirements reduces risk and avoids late rework or costly incidents.

### II. Decentralized Distribution & Interoperability
When applicable, features that involve decentralized distribution (peer-to-peer, content-addressed storage, federated services) MUST document distribution/topology choices, trust model, and upgrade/migration strategy. Packages and releases intended for decentralized delivery SHOULD include reproducible builds, signed artifacts, and clear peer discovery/bootstrapping guidance. Interoperability contracts (wire formats, protocols) MUST be versioned and backward-compatible when possible.

Rationale: Decentralized systems introduce different failure modes and trust boundaries. Explicit documentation and signed artifacts are required to ensure reliable distribution and consumer safety.

### III. Blockchain & Smart Contract Safety (when applicable)
Blockchain-integrated features MUST separate on-chain and off-chain responsibilities, minimize on-chain complexity, and include formal review/audit for any on-chain code. Gas/fee considerations, replay and oracle attack mitigations, and transaction failure modes MUST be documented. Smart contracts or chain code MUST follow security checklists and include test suites that exercise failure and upgrade paths. Any economic or financial logic MUST require an explicit business and legal review before deployment.

Rationale: On-chain code is immutable by default and often controls value; rigorous review, tests, and audits reduce risk of catastrophic failures.

### IV. Open Source Ethos & Licensing
The project embraces open-source principles: contributions SHOULD be encouraged, licenses must be explicit, and contributor guidelines MUST be clear. All third-party dependencies MUST have compatible licenses and be recorded. Releases and major design changes SHOULD include communication plans for downstream consumers. Governance for community contributions and maintainers MUST be documented (CLA, code of conduct, maintainership rules where applicable).

Rationale: Clear licensing and community rules enable broader adoption, protect contributors, and reduce legal risk.

### V. Existing Operational Principles (Quality, Testing, Observability)
Previously established principles for code quality, test-first development, UX, performance budgets, and observability remain in force and MUST be applied alongside the domain-specific principles above. Tests, linters, CI gates, performance budgets, structured logging, and semantic versioning remain required practices.

Rationale: Security, decentralization, and open-source practices complement and build on existing engineering quality gates.

## Additional Constraints
- Licensing: Every release MUST include a LICENSE file and a dependency license manifest.
- Secrets & Keys: Private keys and credentials MUST be stored in approved secret stores; clear rotation policies MUST be documented.
- Audits: Any production smart contract or critical cryptographic module MUST have either a third-party audit or documented internal audit and remediation plan.

## Development Workflow & Quality Gates
- All feature specs MUST include a Security Considerations section and indicate if decentralized distribution or blockchain elements apply.
- Plan and tasks generation tools MUST check for security, licensing, decentralization, and audit tasks and refuse to proceed without explicit justification or exception.
- CI gates MUST include dependency scanning, static security analysis, test suite, license checks, and basic performance smoke tests where applicable.

## Governance
- Amendments that add or materially change security, licensing, or distribution rules are a MINOR bump.
- MAJOR bump is reserved for incompatible redefinitions of governance or principle removals.
- Editorial/formatting fixes are PATCH bumps.

Approval policy:
- Security-affecting amendments MUST include at least one security reviewer and one maintainer approver.

**Version**: 2.3.0 | **Ratified**: 2025-09-24 | **Last Amended**: 2025-09-24