# Privacy Policy

Effective Date: 2025-09-25

This Privacy Policy describes how the self-hostable Pay2Slay Faucet (the "Software") processes user data. The goal is maximum privacy and minimal data retention. Deployers ("Operators") are expected to follow or improve upon these principles.

## Guiding Principles
- Data Minimization: Only store what is strictly required for correct reward calculation, abuse prevention, and auditability.
- Local-Only by Default: No telemetry, ad, or tracking beacons are emitted upstream. All metrics/traces stay within the operator’s infrastructure unless explicitly configured otherwise.
- Ephemerality: Volatile or derivable data (e.g., session state, transient OAuth exchanges) is not persisted beyond functional need.
- User Transparency: Data categories and purposes are documented below; no hidden processing.
- Opt-Out Friendly: Optional features (tracing export, extended analytics) are disabled unless the operator enables them.

## Data Categories
| Category | Examples | Purpose | Retention | Notes |
|----------|----------|---------|-----------|-------|
| Identity (Discord) | discord_user_id, username, guild membership flag | Eligibility + attribution for rewards | Until account deletion request or operator purge | No privileged scopes requested beyond identity+guild check. |
| Identity (Fortnite) | epic_account_id | Matching activity to user for kill deltas | Until account deletion or unlink | Sourced via Yunite mapping; not shared externally. |
| Wallet | Banano address (primary) | Deliver payouts | Until unlink or deletion | Multiple addresses optional; only primary used for payouts. |
| Reward Activity | RewardAccrual (kills, amount, epoch_minute) | Compute payouts / audit abuse | Until settled + (operator-defined audit window) | Could be pruned after payout finalization if operator chooses. |
| Payout Records | amount, tx_hash, status, attempt metadata | Financial accountability / retry / dispute resolution | Indefinite or operator-defined ledger retention | tx_hash may be public on-chain anyway. |
| Verification Events | VerificationRecord (source, status, timestamps) | Trace verification history / dispute resolution | Rolling window or indefinite per operator | Can be aggressively trimmed (keep last successful). |
| Abuse Flags | flag_type, severity, detail | Protect fair usage / integrity | Until cleared or user deletion | Only heuristic summaries; no raw IP storage. |
| Region Code (coarse) | e.g., "eu", "na" | Abuse analytics, payout distribution stats | Optional; can be disabled | Derived from header or coarse IP mapping; never precise geo. |
| Logs (Structured) | event names, trace/span IDs (if enabled) | Debug & audit | Short retention recommended (e.g., 7–30 days) | Exclude secrets via masking helper. |
| Sessions | HMAC session token (cookie) | Authenticate subsequent requests | In-memory / cookie TTL only | Tokens are opaque & revocable by clearing cookie. |

## What We Deliberately Do NOT Collect
- No email, real name, date of birth, government ID, phone number.
- No precise geolocation, IP retention, or third‑party analytics IDs.
- No behavioral profiling or marketing segmentation.
- No biometric or sensitive category data.

## Optional / Operator-Controlled Features
| Feature | Default | Privacy Impact | Mitigation |
|---------|---------|----------------|------------|
| OpenTelemetry Export | Disabled | Could export spans (includes route names, timing) | Keep export endpoint internal or keep disabled |
| Extended Region Middleware | Enabled (coarse only) | Minimal coarse region code | Disable via config if undesired |
| Metrics Endpoint (/metrics) | Enabled | Exposes aggregated counters | Protect via network policy / auth gateway |
| Tracing IDs in Logs | Enabled (local) | Correlates request events | Avoid exporting logs to third parties without review |

## Data Subject Controls
Operators should provide (through their deployment channel):
- Right to Access: Endpoint or process for user to view stored identity & payout history (already partially covered by existing endpoints `/me/status`, `/me/payouts`).
- Right to Erasure: Operator script or admin action to delete (or anonymize) user, cascading to wallet links, accruals (settled), flags, sessions.
- Right to Rectification: Re-trigger verification to refresh epic mapping (/me/reverify or admin reverify).

## Security Measures
- Session tokens signed with HMAC secret (not guessable; no PII inside).
- Secrets masked in structured logs (`safe_dict`).
- Rate limiting & abuse heuristics reduce automated scraping/enumeration.
- Optional operator balance guard prevents unintended empty payouts.

## Retention Guidance (Recommended)
| Data | Suggested Max Retention | Disposal Method |
|------|-------------------------|-----------------|
| Raw Accrual Rows | 30–90 days post-settlement | Delete or aggregate stats only |
| Verification Records (older than last success) | 30 days | Purge | 
| Abuse Flags (resolved) | 90 days | Purge |
| Logs | 7–30 days | Rotate + shred |
| Metrics TSDB | 30–90 days | Retention policy |

## International & Transfers
The Software does not transmit data off the operator’s infrastructure unless explicitly configured (e.g., external tracing endpoint). Any cross-region transfer considerations fall to the operator’s hosting choices. No automated overseas transfer logic exists in the code.

## Children’s Data
The Software is not designed to collect age indicators; operators should restrict promotion to appropriate audiences per their jurisdiction.

## Changes to This Policy
Versioned in source control. Material changes should increment Effective Date and summarize differences in commit messages.

## Contact / Governance
As a self-hosted project, governance and compliance responsibilities rest with each operator. Community contributions to strengthen privacy are welcome via pull request.

## Quick Operator Checklist
- [ ] Disable OTLP export unless needed
- [ ] Protect /metrics behind auth or network policy
- [ ] Set log retention ≤30d
- [ ] Provide documented user deletion procedure
- [ ] Periodically prune settled accruals & stale verification records
- [ ] Review configs for accidental secret exposure

---
This policy aims for maximal privacy with minimal friction. If you can remove or anonymize more while keeping rewards accurate—do it, and contribute improvements.
