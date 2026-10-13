# Deployment and rollback notes

## Current deployment shape

Render declares a Python web service rooted at backend/ and a managed PostgreSQL database. Build generates a deterministic synthetic dataset and trains/calibrates a model artifact. Startup creates missing tables through SQLAlchemy; it does not run Alembic migrations automatically. Configure secrets on the host, never in source or client-side NEXT_PUBLIC variables. The environment template at ../.env.example contains placeholders only.

## Pre-deploy checks

1. Use a staging database and synthetic data only.
2. Back up the database and record the current service revision and model artifact version.
3. Run alembic upgrade head from backend/ before starting the new app. Inspect generated SQL and test against a restored staging backup first.
4. Generate, calibrate and train the synthetic artifact. Keep the previous artifact immutable for rollback.
5. Configure API_KEY_SECRET, SESSION_SIGNING_SECRET (at least 32 random characters), ANALYST_EMAIL, ANALYST_PASSWORD_HASH, DATABASE_URL, CORS_ORIGINS and required settings on the host. Never print secret values.
6. Run backend tests, integration simulator and frontend build. Verify health, readiness, login, score, retrieval, cases and audit.
7. Confirm origins, production credentials, backups and monitoring. Current global key and unscoped records block multi-institution data.

## Rollback

1. Stop promotion and route traffic to the prior service revision/image.
2. Restore the prior model artifact/version if the rollback is caused by model behavior; never overwrite the old artifact during evaluation.
3. Keep database schema changes additive and backward compatible. Do not use destructive downgrade/drop as rollback. If a migration is incompatible, restore the pre-deployment backup to an isolated database and use the host's reviewed recovery process.
4. Verify readiness and the known-good synthetic scoring fixture, then review error logs for the affected window.

This is a procedure, not a verified live deployment. No live deploy or rollback was performed for this revision.
