# CERVIQON Current State Audit

Audit date: 2026-10-14. Repository: TrustSentinel, branch main, HEAD 194551f (Updated the ML model). Working tree is clean except the user-provided untracked backend/data/fresh_evaluation/implementationprompt.md, preserved.

## Scope and test limits

Inspected repository structure, tracked files, routes, scoring services, model contract, evaluation scripts, persistence models, auth/configuration, frontend and deployment. No application behavior was changed during this baseline audit.

Baseline execution was blocked: shell runner fails during setup with helper_unknown_error; node process runner returns python spawnSync EACCES and npm ENOENT. my-app/node_modules, backend/models, backend/data/generated and backend/data/synthetic are absent. Thus backend tests and frontend build were NOT RUN; no pass is claimed. Runtime findings need confirmation in a supported environment.

## Architecture and workflow

- Frontend: Next.js Pages Router, React 19, TypeScript 5, Next 16. Login and dashboard live under my-app/pages; API calls use my-app/lib/api.ts and NEXT_PUBLIC_API_BASE_URL. Browser session token is stored in sessionStorage.
- Backend: FastAPI, Pydantic Settings, SQLAlchemy 2, Alembic; SQLite default and PostgreSQL URL normalization. Entry points are backend/app/main.py, core/config.py and db/database.py.
- Scoring: dashboard score form -> POST /v1/risk/score -> RiskRequest -> score_transaction -> account history from extract_features -> shared 17-feature builder -> rules and optional calibrated Isolation Forest -> hybrid_score -> bands/actions -> persistence of transaction, signals, decision, intervention, case and audit -> JSON response.
- Feature contract: trustsentinel-context-v2. Training and inference share backend/app/ml/features.py. Synthetic generation splits accounts 60/20/20; training, calibration and held-out evaluation scripts exist. Checkout contains no model artifact or generated evaluation dataset/report.
- Deployment: Render rootDir backend; build generates, calibrates and trains synthetic model. Startup uses SQLAlchemy create_all; Alembic migration exists. Dockerfile and GitHub Actions evaluation workflow exist.

Data flow: Dashboard score form and external client -> POST /v1/risk/score -> API key or bearer auth -> RiskRequest validation -> score_transaction -> account transaction history -> shared 17-feature builder -> rules and optional Isolation Forest -> hybrid score/threshold -> decisions, signals, cases, audit -> advisory response -> UI/client.

Manual form sends transaction, account, beneficiary and device IDs, amount, currency and channel; timestamp is optional and defaults to UTC. Currency is uppercased. History is account scoped. Existing decisions are returned on transaction ID before payload equivalence is checked. New entities can be provisioned. Service commits database writes; DB errors use generic safe 500 handling, while rollback and uniqueness races lack executed coverage.

## Route inventory

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | /health | Public | Liveness |
| GET | /ready | Public | DB probe and model/fallback status |
| POST, GET | /v1/auth/login, /v1/auth/session | Public login, bearer session | Analyst authentication |
| POST | /v1/risk/score | API key or bearer | Risk assessment |
| POST | /v1/sandbox/scenario | API key or bearer | Synthetic backend scenario |
| GET | /v1/transactions, /v1/transactions/{transaction_id} | API key or bearer | Read transactions |
| GET | /v1/cases, /v1/cases/{case_id} | API key or bearer | Read cases |
| POST | /v1/cases/{case_id}/outcome | API key or bearer | Record analyst outcome |
| GET | /v1/metrics/summary | API key or bearer | Global aggregate metrics |
| GET | /v1/audit | API key or bearer | Audit events |

FastAPI generates /openapi.json and /docs; no checked-in OpenAPI artifact was found.

## Findings

| ID | Status / severity | Finding and impact | Evidence |
|---|---|---|---|
| A1 | Implemented / positive | Manual scoring, scenario simulator, cases, transaction details, audit and metrics UI exist and call backend. | my-app/pages/dashboard, my-app/lib/api.ts |
| A2 | Implemented / positive | Shared deterministic feature extraction, rules, optional ML, versions, reason signals and persistence exist. | backend/app/services/risk_service.py, backend/app/ml/features.py, backend/app/risk_engine |
| A3 | Partially implemented / high | Authentication has API-key and analyst bearer paths, but neither has institution identity. A configured key/session can access global records and metrics; no tenant fields exist. Unsafe for multi-institution data. | core/security.py; transactions/cases/audit/metrics routes; models.py |
| A4 | Partially implemented / high | Idempotency is global by transaction ID. Same ID with changed payload silently returns old assessment; no tenant namespace or concurrency check is evident. | risk_service.py; globally unique transaction ID |
| A5 | Partially implemented / high | Response omits assessment/decision ID, explicit completeness/cold-start, lifecycle event stage and documented amount minor-unit contract. | risk schema and service response |
| A6 | Partially implemented / medium | First-time beneficiary is a weighted rule (default 20) and reason. Alone it scores low with rules-only defaults, but interaction with ML/policy is untested; completeness is not explicit. | risk_engine/rules.py; feature_service.py |
| A7 | Partially implemented / medium | X-Request-ID is generated/echoed but not persisted with decision; logs contain transaction identifiers. | main.py; risk_service.py |
| A8 | Partially implemented / medium | Readiness checks DB and reports rules-only fallback. Startup create_all is not schema migration for existing deployments. | health.py; main.py; Alembic |
| A9 | Partially implemented / medium | In-memory per-process IP rate limit is not tenant-aware/distributed; proxy identity needs deployment validation. | core/rate_limit.py |
| A10 | Implemented with limitations / positive | Training/serving share features; generator splits accounts and evaluator checks 2,000-row holdout and dataset hash. Evidence remains synthetic. | features.py, generate_data.py, train_model.py, evaluate_model.py |
| A11 | Not verified / blocker | No model/evaluation artifacts or runtime/dependencies accessible; baseline tests and build cannot execute in this environment. | Missing generated dirs and node_modules; process failures |
| A12 | Missing / high | No separate external synthetic integration client; dashboard simulator calls scenario endpoint, not an independently authenticated client. | No client project/scripts |
| A13 | Partially implemented / medium | API docs exist, but no version-controlled OpenAPI contract or external guide for tenant onboarding, retries, errors, timeout and compatibility. | backend/docs/api.md; generated FastAPI OpenAPI |
| A14 | Missing / launch blocker | Root redirects to login; no public Cerviqon website, approved brand asset, privacy/legal policy or configured contact workflow. | my-app/pages/index.tsx; public assets |
| A15 | Partially implemented / medium | Outcomes include confirmed scam, legitimate, needs review, escalated; no explicit false-positive label. Not automatically used for training. | schemas/risk.py; cases.py |
| A16 | Partially implemented / medium | Structured errors and extra-field rejection exist. Logs avoid bodies but contain identifiers; retention and identifier handling are undefined. | core/errors.py; main.py; risk_service.py |
| A17 | Implemented / positive | Product states advisory only and does not execute/block payments; simulated totals are labeled. | README and metrics route |
| A18 | Partially implemented / medium | Brand rework required; source, storage keys, deployment names, docs and login still say TrustSentinel. Compatibility needs careful migration. | tracked files |

## Capabilities to preserve

Preserve dashboard routes/login, scoring form, backend scenario lab, case/outcome workflow, transaction details, audit/metrics, existing FastAPI routes, SQLite and PostgreSQL support, rules-only fallback, current model format if restored, and account-disjoint synthetic evaluation. Do not overwrite model artifacts or user data.

## Prioritized plan and acceptance criteria

1. P0 environment/baseline: restore Python, Node and dependencies; run current suite/build and record real results.
2. P0 scoring: add regression coverage for valid/invalid scoring, persistence/retrieval, retries, changed-payload duplicate IDs, model outage and DB failure; return traceable assessment ID and explicit conflict semantics.
3. P0 tenant/security: define client institution identity, scope writes/read APIs/metrics/audit and cases; prove client A cannot read/mutate client B data, including duplicate IDs. Use additive documented migration/backfill.
4. P1 integration contract: publish OpenAPI/schemas, amount/currency, idempotency, optional context, timeout/errors, correlation and advisory semantics; external synthetic client calls actual API.
5. P1 context/reasons: completeness/cold-start; test first-time beneficiary alone and ensure reason codes correspond to real score contributors; no cross-institution pooling.
6. P1 evaluation/security: reproducible synthetic evaluation and integration tests for auth, isolation, retries, latency and failures; document synthetic limitations.
7. P1 docs/gate: setup, API, evaluation, security, deployment/rollback, known limitations and env placeholders; all MVP criteria recorded pass or exact blocker.
8. P2 public site only after gate: maintain dashboard compatibility, truthful claims, responsive/accessibility/build verification. Contact/legal/brand inputs must be evidenced.

## Baseline execution results

- python -m pytest -q from backend: NOT RUN; process launch blocked (python EACCES; shell setup failure).
- npm run build from my-app: NOT RUN; npm unavailable and dependencies absent.
- Static inspection: completed; no application behavior changed during audit.


## Implementation follow-up (after baseline)

The original Phase 0 findings above are retained as baseline. Later changes added request/assessment IDs and cold-start status to the score response, persisted those fields in risk-decision audit metadata, rejected changed-payload transaction-ID reuse with 409, added a real-backend synthetic integration client, updated the response schema/docs/dashboard, and added regression assertions. These changes are not runtime verified. The original A4 and A5 risks are addressed at the direct scoring endpoint for single-tenant operation, subject to testing. A3 tenant isolation remains a release blocker; A11 test/build/evaluation remains unverified. The acceptance-gated landing page has not been built. Full gate status is in docs/MVP_IMPLEMENTATION_SUMMARY.md.


## Post-baseline implementation review — 2026-10-14

The findings above describe the preserved Phase 0 baseline and are not a current-state report. Subsequent implementation added institution principals and per-institution API keys, tenant ID mapping and migration, scoped scoring and read/write routes, request/assessment traceability, idempotency conflict behavior, the direct scoring contract, a real-backend integration simulator, and false-positive case outcomes. Scenario tests and the synthetic evaluator were updated to query mapped transaction IDs. Generated OpenAPI now describes API-key and bearer alternatives.

Code review also found and corrected an indentation syntax error in the backend security test file. The Windows environment denied execution of its available Python executable; tests, migrations, evaluation, and production build have therefore not been executed. Treat all changes as implemented but runtime-unverified. Phase 7 remains gated on an acceptance pass; it has not been started. Current acceptance and verification statuses are in docs/MVP_IMPLEMENTATION_SUMMARY.md.
