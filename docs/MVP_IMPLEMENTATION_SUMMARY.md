# Cerviqon MVP implementation and delivery report

Status date: 2026-10-14. Baseline audit: docs/audit/CERVIQON_CURRENT_STATE_AUDIT.md. This report distinguishes implemented code from runtime verification.

## Phase status

| Phase | Status | Work and evidence |
|---|---|---|
| 0 — Repository audit | Complete | Baseline architecture, workflows, scoring path, routes, evaluation pipeline and findings recorded in the audit report. Findings remain labeled as baseline. |
| 1 — Stabilize product | Implemented in code; tests not run | Shared scoring path retained; response contract, idempotent retries/conflict, scoped persistence and retrieval, model-fallback errors, correlation IDs and versioned audit metadata are present. Corrected test syntax and tenant-mapped test queries. |
| 2 — Integration API | Implemented in code; not runtime verified | POST /v1/risk/score is the shared dashboard/client service. API keys and analyst sessions resolve institution identity; OpenAPI describes API-key and bearer authentication. Contract and synthetic examples are in backend/docs/api.md. |
| 3 — Context and explanations | Implemented in code; tests not run | Account history is tenant-scoped; cold-start status and real rule/model reason evidence are returned. Added distinct FALSE_POSITIVE, LEGITIMATE, CONFIRMED_SCAM, NEEDS_REVIEW and ESCALATED investigation outcomes. Feedback is not automatically used in model training. |
| 4 — Integration simulator | Implemented; not executed | backend/scripts/simulate_integration.py submits synthetic fixtures and retries to the actual API. |
| 5 — Evaluation and security | Scripts and controls implemented; evaluation/tests not run | Account-disjoint synthetic pipeline and holdout evaluator exist. No dataset/model artifact/report was generated in this environment, so no metrics are claimed. Tenant regression coverage includes scoring, ID collision, history, transaction reads, cases/outcomes, audit and metrics. |
| 6 — Documentation and acceptance gate | Documentation updated; gate not passed | Setup, architecture/data flow, API, integration, evaluation limitations, deployment, rollback and security readiness are documented. Runtime test, migration and build criteria remain unverified. |
| 7 — Public landing page | Not started; correctly held at acceptance gate | The implementation brief forbids beginning the public website until the MVP acceptance gate passes. Contact/legal destinations are also not configured. |
| 8 — Final delivery report | Complete as a status report | Results and blockers are stated below. No local tests or live deployment are claimed. |

## Implemented changes

- Per-institution server-side API key mapping via INSTITUTION_API_KEYS_JSON; analyst assignments via ANALYST_USERS_JSON and signed tenant-scoped sessions.
- Reserved legacy default tenant for existing rows and compatibility settings; production with missing credentials fails closed.
- Additive Alembic migration assigns existing rows to default and adds tenant identifier mappings. Render and Docker run migrations before the API; local setup instructions include the migration step.
- Institution-scoped IDs and query filters for scoring, feature history, transactions, cases/outcomes, interventions, audit and metrics. Per-tenant mappings prevent identical external IDs from colliding.
- Stored feature-schema and hybrid-policy versions are replayed with the original assessment. Request/assessment IDs, completeness and changed-payload conflict behavior are exposed.
- API and analyst dashboard use the same scoring engine; the simulator calls the live API, not a fabricated response.
- Added FALSE_POSITIVE investigator outcome; reviewer outcomes remain separate from model-training data.
- Corrected integration tests and evaluation queries to account for mapped internal transaction IDs; added tenant assertions for cross-institution reads/writes and aggregates.

## Verification results

| Check | Result |
|---|---|
| Backend test suite | NOT RUN. Windows denied execution of C:\Users\DELL\python312\python.exe (Access is denied); the WindowsApps python shim is also inaccessible. |
| Database migration | NOT RUN for the same Python runtime restriction. |
| Synthetic training/evaluation | NOT RUN. No evaluation metrics or model artifact are present in this checkout. |
| Integration simulator/manual workflows | NOT RUN; require backend runtime and configured development credentials. |
| Frontend lint/production build | NOT RUN. The Node installation directory contains npm shims but no node.exe; frontend dependencies are absent. |
| Deployment/browser/responsive/accessibility checks | NOT RUN. No live deployment or usable browser test runtime was available. |
| Static whitespace check | PASSED: git diff --check exit code 0 after the final code edits. Git emitted only working-copy line-ending warnings. |

## Acceptance gate and release blockers

The gate has not passed. The scoring, persistence, authentication, tenant-isolation, failure, latency, integration simulator, synthetic evaluation, frontend build and security acceptance checks must be executed in a supported environment. The test source itself is not evidence of a passing test. Test the additive migration against a restored staging database before serving institution data.

Security controls still incomplete or deployment-dependent include distributed tenant-aware rate limiting, data retention/deletion, production key rotation and storage-encryption verification. Do not use real institution data or describe the prototype as production-ready. Synthetic metrics, when generated, must be labeled as proxies for synthetic labels rather than real-world fraud performance.

Phase 7 remains unstarted because the brief requires the acceptance gate to pass first. The repository also has no approved contact destination or privacy/legal pages, so a truthful public CTA/footer cannot yet be configured. Continue with the test/build/migration acceptance work before authoring or publishing that site.

## Reproduction commands

From backend/ in a Python 3.11+ environment with requirements installed:

    alembic upgrade head
    python -m pytest -q
    python scripts/generate_data.py
    python scripts/calibrate_policy.py
    python scripts/train_model.py
    python scripts/validation_experiments.py
    python scripts/evaluate_model.py
    python scripts/simulate_integration.py --scenario cold-start --repeat

For the simulator, start the API and configure CERVIQON_API_URL and CERVIQON_API_KEY with development-only synthetic credentials.

From my-app/ in a supported Node environment:

    npm ci
    npm run lint
    npm run build

## Operator configuration

Configure DATABASE_URL, APP_ENV, CORS_ORIGINS, INSTITUTION_API_KEYS_JSON (unique per-institution keys), ANALYST_USERS_JSON (password hashes and institution IDs), SESSION_SIGNING_SECRET (at least 32 random characters), and model/policy settings on the server. API_KEY_SECRET and the legacy analyst settings are reserved for default-tenant compatibility. Keep values out of source control, browser bundles and logs. See backend/.env.example for placeholders.
