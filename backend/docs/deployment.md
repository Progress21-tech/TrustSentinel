# Deployment and rollback notes

## Current deployment shape

Render declares a Python web service rooted at backend/ and a managed PostgreSQL database. Build generates a deterministic synthetic dataset and trains/calibrates a model artifact. Startup runs alembic upgrade head before Uvicorn in the provided Dockerfile and Render configuration. SQLAlchemy creates missing tables as a local-development convenience; Alembic remains the production schema migration path. Configure secrets on the host, never in source or client-side NEXT_PUBLIC variables. The environment template at ../.env.example contains placeholders only.

## Pre-deploy checks

1. Use a staging database and synthetic data only.
2. Back up the database and record the current service revision and model artifact version.
3. Back up the staging database, run alembic upgrade head from backend/, and verify the additive tenant migration against a restored staging copy before serving traffic.
4. Generate, calibrate and train the synthetic artifact. Keep the previous artifact immutable for rollback.
5. Configure INSTITUTION_API_KEYS_JSON with unique per-institution secrets and ANALYST_USERS_JSON with password hashes and institution assignments. Set SESSION_SIGNING_SECRET (at least 32 random characters), DATABASE_URL, CORS_ORIGINS, and model settings. API_KEY_SECRET plus legacy analyst settings are retained for the reserved default tenant only. Never print secret values.
6. Run backend tests, integration simulator and frontend build. Verify health, readiness, login, score, retrieval, cases and audit.
7. Confirm origins, distinct production credentials, backups and monitoring. Do not onboard institution data until the tenant tests and migration have passed in staging.

## Rollback

1. Stop promotion and route traffic to the prior service revision/image.
2. Restore the prior model artifact/version if the rollback is caused by model behavior; never overwrite the old artifact during evaluation.
3. Keep database schema changes additive and backward compatible. Do not use destructive downgrade/drop as rollback. If a migration is incompatible, restore the pre-deployment backup to an isolated database and use the host's reviewed recovery process.
4. Verify readiness and the known-good synthetic scoring fixture, then review error logs for the affected window.

This is a procedure, not a verified live deployment. No live deploy or rollback was performed. Windows denied execution of the Python binary in this environment, so the migration and test suite still require a supported runtime.
