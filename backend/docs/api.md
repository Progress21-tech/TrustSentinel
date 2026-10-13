# API integration guide

The FastAPI service publishes its machine-readable OpenAPI document at /openapi.json and interactive docs at /docs.

## Assess a synthetic or authorized transaction

POST /v1/risk/score accepts X-API-Key for a configured server-to-server client or the existing analyst bearer session. The current deployment has one shared API key and is **single-tenant only**; institution-level authorization and data isolation are not implemented. Do not send real institution data to this prototype or share the shared key between institutions.

Required JSON fields: transaction_id, account_id, positive amount, beneficiary_id, device_id, and channel (mobile_app, web, ussd, api). currency defaults to NGN. Amount is expressed in major currency units (for NGN, naira); this prototype persists amounts to two decimal places. timestamp is optional ISO-8601 and defaults to server UTC. IDs must be pseudonymous references; do not send account numbers. Account identifiers are provisioned as synthetic entity records if absent. Optional feature vectors and unsupported event lifecycle fields are rejected.

Example fixture (synthetic only):

    {"transaction_id":"synthetic-txn-001","account_id":"synthetic-acct-001","amount":1250.00,"currency":"NGN","beneficiary_id":"synthetic-ben-001","device_id":"synthetic-device-001","channel":"api"}

A successful response includes assessment_id, request_id, data_completeness, risk_score, risk_band, recommended_action, reason_codes, evidence, model/policy versions and optional case_id. It is an advisory assessment, not confirmed fraud and not a payment authorization or block. For cold-start history, status is cold_start. First-time beneficiary is a contextual signal and is not proof of fraud.

Repeated requests with the same transaction_id and same facts return the persisted assessment. Reusing that ID with different account, amount, currency, beneficiary, device, channel or supplied timestamp returns 409 IDEMPOTENCY_CONFLICT. A caller should use stable transaction IDs for retries and a new ID for a new event. X-Request-ID is accepted and returned; a server-generated value is supplied when absent.

Validation returns 422; missing/invalid credentials return 401 (or 503 when production auth is unconfigured); changed-payload idempotency returns 409; model-required failure returns 503; database/unexpected failure returns a generic 500. Clients should set a finite timeout and retry network errors with the same transaction ID. Rate limits are currently per process/IP.

## Integration simulator

From backend/, start the API in a supported environment, configure CERVIQON_API_URL and CERVIQON_API_KEY (development/test values only), then run:

    python scripts/simulate_integration.py --scenario cold-start --repeat

Choices are cold-start, established and high-value. This client uses Python's standard library and submits directly to the actual endpoint. The API provisions unseen synthetic entities; its scenario labels do not fabricate a response. Never use production credentials or real bank data.

## Other endpoints

- GET /health, GET /ready
- POST /v1/sandbox/scenario with one of the eight stable backend scenario names
- GET /v1/transactions/{transaction_id}, GET /v1/transactions?limit=50
- GET /v1/audit?limit=100
- GET /v1/cases?status=&risk_band=&date=YYYY-MM-DD&outcome=
- GET /v1/cases/{case_id}, POST /v1/cases/{case_id}/outcome
- GET /v1/metrics/summary (aggregates the current single tenant's data)

Known limitation: shared global API/analyst credentials and non-tenant-scoped storage make this unsuitable for multiple institutions. Institution onboarding requires tenant-scoped credentials, an additive migration/backfill, scoped read/write queries, and cross-tenant tests before external evaluation.
