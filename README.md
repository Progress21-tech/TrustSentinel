# TrustSentinel

TrustSentinel is a synthetic-data prototype for identifying contextual indicators associated with potentially socially engineered payments. It returns explainable risk assessments and recommended interventions; it does not process payments or determine customer intent. Scores and prevented-loss figures are prototype/simulated values, not production accuracy claims.

## Run locally

Requires Python 3.11+. By default, local development uses SQLite so the demo starts without an external database. Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL for PostgreSQL (for example `postgresql+psycopg://user:password@host:5432/dbname`).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. `/health` is liveness; `/ready` checks the database and reports whether ML is loaded. When `API_KEY_SECRET` is configured, send it as `X-API-Key` to the protected `/v1` endpoints. Leave it empty only for local development.

## Demo flow

`POST /v1/sandbox/scenario` accepts `normal`, `new_beneficiary_large_amount`, `new_device_large_transfer`, `account_recovery_new_beneficiary`, `rapid_transfers`, `risky_beneficiary`, `combined_high_risk`, and `legitimate_high_value`. Each has stable transaction IDs from the PRD and is safe to repeat. Risk decisions, signals, interventions, cases, and audit events persist in the configured database.

Example:

```json
{"scenario":"combined_high_risk"}
```

List or inspect cases at `/v1/cases`; submit an analyst outcome to `/v1/cases/{case_id}/outcome`. `/v1/metrics/summary` includes explicitly simulated financial totals. `/v1/transactions/{transaction_id}` returns its decision, signals, intervention, and case reference.

For a direct risk request, first seed an account and history (below), then call `POST /v1/risk/score`:

```json
{"transaction_id":"txn_001","account_id":"ACC-00001","amount":850000,"currency":"NGN","beneficiary_id":"BEN-00001","device_id":"DEV-0001","channel":"mobile_app"}
```

Unknown accounts return 404. Beneficiary/device novelty is calculated against that account's own transaction history. Validation errors use a stable `{ "error": { "code", "message" } }` structure.

## Synthetic data and ML

```powershell
python scripts/generate_data.py
python scripts/seed_database.py
python scripts/train_model.py
python scripts/evaluate_model.py
```

Generation is seeded and writes linked entities plus at least 10,000 transactions under `data/synthetic/`. The database seed is idempotent and skips a non-empty customer database. Train the Isolation Forest offline; the API never trains during startup or requests. The generated artifact is ignored by Git. Until an artifact exists or if loading/inference fails, scoring explicitly returns `ml_status: unavailable` and uses the rules-only score.

## Database migrations

For managed environments, set `DATABASE_URL`, then run:

```powershell
alembic upgrade head
```

The application also creates missing tables on startup to keep the MVP demo simple. Production schema evolution should use Alembic migrations.

## API overview

- `GET /health`, `GET /ready`
- `POST /v1/risk/score`
- `POST /v1/sandbox/scenario`
- `GET /v1/transactions/{transaction_id}`
- `GET /v1/cases`, `GET /v1/cases/{case_id}`, `POST /v1/cases/{case_id}/outcome`
- `GET /v1/metrics/summary`

Swagger/OpenAPI is available at `/docs`. See [`docs/api.md`](docs/api.md), [`docs/risk_signals.md`](docs/risk_signals.md), and [`docs/feature_dictionary.md`](docs/feature_dictionary.md).

## Deployment

`render.yaml` defines the Render web service and managed PostgreSQL database. Its build command trains the synthetic Isolation Forest offline; the API does not train at startup or while handling requests. Set `API_KEY_SECRET` in Render. Configure allowed browser origins with `CORS_ORIGINS`. HTTPS is provided by Render's service endpoint. The MVP includes a per-process IP rate limit, but it is not a distributed limiter. It does not implement user login or role-based dashboard access.

## Prototype scoring assumptions

Risk bands follow the PRD thresholds: LOW 0–29, MODERATE 30–59, ELEVATED 60–79, HIGH 80–89, CRITICAL 90–100. Rule weights and the 70/30 rules/ML hybrid formula are documented prototype assumptions. Several expected demo bands in the PRD are unreachable for the listed signals under those weights: new beneficiary + unusual amount yields 40 points (at most 58 with an ML score of 1); new device + unusual amount yields 35 (below HIGH); recovery + new beneficiary + unusual amount yields 55 (at most 68 with an ML score of 1); rapid transfers and risky beneficiary also remain below HIGH without further evidence. The implementation preserves the explicit weights and thresholds and exposes the actual signals and score. Adjust weights using `RULE_WEIGHTS_JSON`, `RULE_SCORE_WEIGHT`, and `ML_SCORE_WEIGHT` when calibrating the demo policy.
