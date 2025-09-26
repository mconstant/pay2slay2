# Security Policy

## Supported Versions
Until first tagged release (>=1.0.0), all commits on the default branch receive security updates.

## Reporting a Vulnerability
Please open a private security advisory on GitHub (Security > Advisories > Report a vulnerability) or email security@example.org with details.

Provide:
- Affected endpoints / components
- Reproduction steps or PoC
- Impact assessment (confidentiality / integrity / availability)

We aim to acknowledge within 48h and provide a fix or mitigation timeline within 5 business days.

## Key Areas
- OAuth state & session HMAC
- Rate limiting (global & per-IP)
- Abuse heuristics & flags (kill rate spikes)
- Payout idempotency and retry safety

## Hardening Roadmap
- Expanded fuzz & replay tests (T055)
- Secrets management audit (T044)
- SBOM + provenance (T057, T058)

## Disclosure
Please practice coordinated disclosure; do not publicize issues before a patch release.
