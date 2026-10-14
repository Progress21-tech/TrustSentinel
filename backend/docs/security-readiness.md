# Security readiness checklist

Status date: 2026-10-14. This is repository inspection, not certification or penetration testing.

| Control | Status | Evidence / follow-up |
|---|---|---|
| Server-side API key | Implemented / not verified | `INSTITUTION_API_KEYS_JSON` maps distinct server-side keys to institution IDs; production fails closed if credentials are absent or invalid. Deployment configuration and rotation still require operator setup. |
| Analyst credentials | Partial | Configured PBKDF2-SHA256 hash and HMAC bearer sessions; rate limit is per process/IP. Verify operational credential policy and session lifecycle. |
| Institution authorization | Implemented / not verified | API-key and analyst principals carry an institution ID; data routes and scoring scope reads/writes by that ID. Verify with the included tests and target database before onboarding. |
| Tenant isolation tests | Added / not run | Cross-tenant scoring, history, same-ID separation, transaction reads/lists and invalid-key tests are in `tests/integration/test_tenant_isolation.py`. Case, outcome, audit and metrics routes are scoped in code; verify them in the deployment test run. |
| Input validation | Partial | Pydantic rejects extra fields and constrains identifiers, amount and channel. Test malformed timestamps, amount boundaries and storage rounding. |
| Transport | Deployment dependent | Verify TLS, custom domains, proxy and origin settings on actual deployment. |
| Storage encryption / key management | NOT VERIFIED | Depends on database and host configuration; repository evidence is insufficient. |
| Sensitive logging | Partial | Logs omit payloads but include transaction IDs and risk summaries. Define pseudonymous identifiers and retention/redaction. |
| Rate limiting | Partial | In-memory per-process IP limiter; not distributed or tenant-aware. Confirm proxy IP and shared limiter for scaled deployment. |
| Data retention/deletion | MISSING | No retention or purge workflow. Define before storing real data. |
| Dependency hygiene | NOT VERIFIED | Requirements are bounded; dependency audit not run. |
| API abuse/error behavior | Partial | Structured errors exist; tests could not run. Add load, concurrency, replay and dependency-failure coverage. |
| Payment execution | Not implemented | API returns advisory assessment; it does not authorize, block or reverse funds. |

Release decision: NOT production ready and not cleared for multi-institution evaluation yet. Tenant authorization and scoping are implemented but require test and target-database migration verification. Operational controls such as distributed tenant-aware rate limiting, retention policy and production monitoring remain incomplete or unverified.
