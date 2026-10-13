# Security readiness checklist

Status date: 2026-10-14. This is repository inspection, not certification or penetration testing.

| Control | Status | Evidence / follow-up |
|---|---|---|
| Server-side API key | Partial | API_KEY_SECRET is backend-only; one shared key is global and production fails closed if missing. Replace with institution-specific credentials before any external institution data. |
| Analyst credentials | Partial | Configured PBKDF2-SHA256 hash and HMAC bearer sessions; rate limit is per process/IP. Verify operational credential policy and session lifecycle. |
| Institution authorization | FAIL | No institution identity in principal or records; protected records and metrics are global. Do not onboard multiple institutions or real data. |
| Tenant isolation tests | NOT RUN / missing | Add cross-tenant tests for scoring, transaction, case, outcome, audit and metrics after defining credential mapping and migrating records. |
| Input validation | Partial | Pydantic rejects extra fields and constrains identifiers, amount and channel. Test malformed timestamps, amount boundaries and storage rounding. |
| Transport | Deployment dependent | Verify TLS, custom domains, proxy and origin settings on actual deployment. |
| Storage encryption / key management | NOT VERIFIED | Depends on database and host configuration; repository evidence is insufficient. |
| Sensitive logging | Partial | Logs omit payloads but include transaction IDs and risk summaries. Define pseudonymous identifiers and retention/redaction. |
| Rate limiting | Partial | In-memory per-process IP limiter; not distributed or tenant-aware. Confirm proxy IP and shared limiter for scaled deployment. |
| Data retention/deletion | MISSING | No retention or purge workflow. Define before storing real data. |
| Dependency hygiene | NOT VERIFIED | Requirements are bounded; dependency audit not run. |
| API abuse/error behavior | Partial | Structured errors exist; tests could not run. Add load, concurrency, replay and dependency-failure coverage. |
| Payment execution | Not implemented | API returns advisory assessment; it does not authorize, block or reverse funds. |

Release decision: NOT production ready and not cleared for multi-institution evaluation. Synthetic local use only until tenant isolation and operational controls are addressed and tested.
