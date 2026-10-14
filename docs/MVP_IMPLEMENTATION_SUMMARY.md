# Cerviqon MVP Implementation Summary

Date: 2026-10-14. Repository branch: main. Baseline: 194551f. See docs/audit/CERVIQON_CURRENT_STATE_AUDIT.md.

## Changes made after the baseline

- Added assessment ID, request correlation ID, and cold-start/history availability to direct scoring responses. Correlation ID and completeness are recorded in the decision audit metadata for replay.
- Made retry behavior deterministic: identical transaction ID and facts return the saved assessment; a reused ID with changed facts returns HTTP 409 IDEMPOTENCY_CONFLICT.
- Exposed the response contract through the direct-risk route's RiskResponse schema and documented major currency units, two-decimal precision, synthetic identifiers, supported fields, errors, retries and timeout expectations.
- Added a separate standard-library Python integration client that calls the real POST /v1/risk/score endpoint and can verify identical retries. It uses synthetic fixtures and a server-configured development key.
- Updated dashboard types and displays with assessment and completeness metadata; added regression assertions for retry/conflict and a first-time-beneficiary-only risk band.
- Updated visible brand copy to Cerviqon while retaining the existing browser session storage key and backend route/configuration compatibility.
- Wrote this summary and updated setup/API documentation.

## Acceptance gate status

| Criterion | Status | Evidence / blocker |
|---|---|---|
| Existing manual scoring workflow | Not verified | Code path preserved and response fields displayed; unable to run the backend or frontend. |
| Validated API request/response | Partially implemented, not runtime verified | Pydantic request/response schema and OpenAPI generation; validation suite unavailable. |
| Dashboard and API share scoring engine | Implemented in code, not runtime verified | Dashboard still uses POST /v1/risk/score, calling score_transaction. |
| Assessment/model/policy traceability | Partially implemented | Assessment ID, request ID and model/policy fields; tenant/version auditing needs verification. |
| Success/failure/cold-start tests | Added assertions, not run | Python executable is inaccessible in this environment. |
| Independent integration simulator | Implemented, not executed | backend/scripts/simulate_integration.py posts to the real API. |
| Reproducible synthetic evaluation report | Not verified | Generator/trainer/evaluator exist, but generated data and model artifact are absent and Python cannot run. |
| Tenant authorization and application-level isolation | IMPLEMENTED / NOT VERIFIED | Per-institution API keys and analyst assignment, tenant-scoped IDs/data/routes, additive migration, and cross-tenant regression tests are implemented; test execution and live database migration remain unverified in this environment. |
| Frontend production build and backend tests | Not run | Python launch blocked; npm PowerShell shim is blocked by execution policy, and npm.cmd cannot find node.exe. |
| Setup, API, integration, evaluation and limitations documentation | Partially implemented | Updated setup/API/simulator docs; deployment/rollback, evaluation report and security-readiness checklist still require evidence. |

The gate has not passed. Phase 7, the public landing page, has therefore not started. A public contact method, privacy/legal links and approved landing-page brand assets are also not available in the repository and must not be invented.

## Known limitations and release blockers

1. Institution/tenant isolation is implemented in code. External evaluation still requires successful execution of the tenant tests and migration against the target database, plus deployment configuration of distinct institution API keys and analyst-to-institution assignments.
2. Backend automated tests could not run: Windows reported that python.exe could not be accessed. The python -m pytest -q attempt exited with an OS launch error.
3. Frontend build could not run: PowerShell blocked npm.ps1 under execution policy; npm.cmd then reported that node was not recognized. The installed Node folder did not contain node.exe at its expected path, and frontend dependencies are absent.
4. No model artifact, generated dataset or evaluation report is present. Synthetic metrics must not be inferred or promoted.
5. Security, persistence, replay/concurrency and browser workflows are unverified. Tenant migration and scoped route code are present but have not been runtime verified.
6. No public privacy/legal policy or real configured contact channel exists. Keep any future landing CTA disabled/configuration-blocked until a real destination is supplied.

## Commands to reproduce in a supported environment

From backend/: python -m pytest -q; python scripts/generate_data.py; python scripts/calibrate_policy.py; python scripts/train_model.py; python scripts/evaluate_model.py; python scripts/simulate_integration.py --scenario cold-start --repeat (with API running and CERVIQON_API_URL / CERVIQON_API_KEY set to development values).

From my-app/: npm ci; npm run build; npm run lint.

No test or build is reported as passed in this environment.


## Institution authorization follow-up

Added `INSTITUTION_API_KEYS_JSON` for institution-specific server-side API keys and `ANALYST_USERS_JSON` for analyst-to-institution assignments. The authenticated principal supplies the tenant scope. Database records have an `institution_id`; external identifiers map to stable opaque tenant-specific identifiers so identical caller IDs do not collide. Existing records migrate to the reserved `default` tenant. Transaction, feature history, case, outcome, audit, and metrics operations include institution filters. Render and Docker startup run Alembic migrations before Uvicorn.

Added `backend/tests/integration/test_tenant_isolation.py` for cross-institution scoring, history, identifier collision, transaction retrieval/listing and unknown-key rejection. Tests could not be run here because `python.exe` is inaccessible in this Windows environment. Therefore this is an implementation report, not a verified security certification; run the backend suite and migration against the deployment database before using institution data.
