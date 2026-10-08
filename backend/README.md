# TrustSentinel

TrustSentinel is a synthetic-data prototype for identifying contextual indicators associated with potentially socially engineered payments. It returns explainable risk assessments and recommended interventions; it does not process payments or determine customer intent. Scores and prevented-loss figures are prototype/simulated values, not production accuracy claims.

## Run locally

Requires Python 3.11+. By default, local development uses SQLite so the demo starts without an external database. Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL for PostgreSQL (for example `postgresql+psycopg://user:password@host:5432/dbname`).
Run commands in this document from the `backend/` directory.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. Swagger UI exposes the existing `X-API-Key` authentication through its **Authorize** button. `/health` is liveness; `/ready` checks the database and reports whether ML is loaded. When `API_KEY_SECRET` is configured, send it as `X-API-Key` to the protected `/v1` endpoints. Leave it empty only for local development.

The environment template is [`.env.example`](.env.example). Copy it to `.env` and adjust `DATABASE_URL`, `API_KEY_SECRET`, `CORS_ORIGINS`, `MODEL_PATH`, and the scoring/model settings as needed. Do not commit `.env` or put real secrets in the template.

## Tests

Install the development dependencies and run the suite from `backend/`:

```powershell
python -m pytest
```

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
python scripts/calibrate_policy.py
python scripts/train_model.py
python scripts/validation_experiments.py
python scripts/evaluate_model.py
```

Generation is seeded and writes linked synthetic entities plus 10,000 transactions under `data/synthetic/`. Entire accounts are assigned to one 60/20/20 train/validation/test split, so an account's history cannot cross splits. The database seed is idempotent and skips a non-empty customer database. The API never trains during startup or requests. The v2 artifact is saved separately as `models/isolation_forest_v2.joblib`; the prior v1 artifact is never overwritten. Artifacts and generated data are ignored by Git. Until a compatible artifact exists or if loading/inference fails, scoring explicitly returns `ml_status: unavailable_rules_only` and uses the rules-only score.

### ML scoring details

The model is an **Isolation Forest**, a lightweight unsupervised anomaly detector suited to a synthetic prototype where labelled examples are limited. It learns only background rows from the reproducible training split. Scenario names, split markers, and labels are never features. The persisted sklearn pipeline applies `StandardScaler` before Isolation Forest inference.

The canonical contract is [`docs/feature_dictionary.md`](docs/feature_dictionary.md), schema `trustsentinel-context-v2`, with 17 features. Training generation and live scoring share `extract_feature_context` in [`app/ml/features.py`](app/ml/features.py). It derives transaction velocity, familiarity, amount ratio, entity ages, and account activity from prior events/entity state. `has_account_history` distinguishes a measured ratio of 1 from the no-history fallback ratio of 1. Features without live sources (session telemetry and graph degrees) were removed. The API accepts transaction facts; callers cannot provide model feature values.

Training uses only normal/background rows in the train split and a fixed generation seed. Defaults remain 200 estimators, `max_samples=auto`, `contamination=auto`, and `max_features=1.0`; `ML_N_ESTIMATORS`, `ML_RANDOM_STATE`, `ML_MAX_SAMPLES`, `ML_CONTAMINATION`, and `ML_MAX_FEATURES` configure the prototype. The new artifact defaults to `models/isolation_forest_v2.joblib` and `iforest-v2.0.0`. It records the dataset SHA-256, generation seed, schema, split counts, feature names, training counts, scaler means/scales, estimator settings, calibration, and selected policy. The v1 artifact path remains distinct for rollback. Artifacts are generated during setup/deployment build rather than committed.

Isolation Forest's raw `decision_function` is calibrated against sorted scores from train-normal rows. Validation compares the empirical lower-tail rank with a training-normal-tail excess mapping and selects calibration, rules/ML weights, and a high-risk threshold from the documented candidate ranges. The selected method, cutoff, weights, and threshold are recorded in the artifact. The risk band uses that same selected threshold. These are synthetic validation decisions, not claims of real-world fraud probability. The ML score is an anomaly contribution, not a fraud probability.

If the artifact is missing, incompatible, or inference fails, the API explicitly returns `ml_score: null`, `ml_status: unavailable_rules_only`, and `model_version: rules-only` when `RULES_ONLY_FALLBACK=true`. With fallback disabled, scoring returns 503. When active, the response includes the loaded model version and `feature_schema_version`. `ML_ANOMALY_REASON_THRESHOLD` controls when the calibrated tail is recorded as an evidence signal; the model never creates free-form explanations.

Run `python scripts/validation_experiments.py` after training for controlled one-factor and cold-start feature comparisons using validation rows only. It records feature vectors, standardized vectors, raw forest scores, calibration ranks, ML/rules/hybrid scores, and actions in `data/generated/validation_experiments.json`. Then `python scripts/evaluate_model.py` evaluates the held-out split once after selections are finalized. It reports rules-only, ML-only, hybrid metrics, score distributions, per-scenario results, latency, and local API persistence behavior in `data/generated/evaluation_report.json`. The v1 artifact is absent from this checkout, so the report marks old-deployed-vs-new comparison unavailable instead of inventing old scores.

The historical v1 GitHub Actions report is summarized in [`docs/calibration_baseline.md`](docs/calibration_baseline.md). Its feature schema and artifact differ from v2, so it is context only and not an old-vs-new comparison on the v2 test population. Synthetic metrics are proxies, not production fraud-detection accuracy on Nigerian financial institution data.

`calibrate_policy.py` uses only train-normal and validation rows for selection. It checks account-disjoint split integrity, evaluates 55–65 high-risk boundaries, five rule/ML weight pairs, and four calibration options, then records whether precision and legitimate-scenario safety targets were met. It does not tune from the test rows. The pipeline reports the selected settings even if targets are missed; it does not force a target result. Artifacts and reports remain under ignored `data/generated/` and `models/` paths.

Known limitation: v2 is trained and validated on deterministic synthetic behavior only. A well-aligned synthetic pipeline does not establish real-world fraud performance or validate the quality of stored beneficiary risk scores. Do not deploy based solely on synthetic metrics.

The frontend should display the backend's `risk_score`, `risk_band`, `recommended_action`, `reason_codes`, and `explanation`; it must not repeat feature engineering or scoring. The API reports actual rule and ML contributions, but the recommendation remains the backend policy result.

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

## Docker

Build with the backend directory as the Docker build context, then run the image:

```powershell
docker build -t trustsentinel-api .
docker run --rm -p 8000:8000 --env-file .env trustsentinel-api
```

The Dockerfile installs `backend/requirements.txt`, trains the synthetic model during image build, and starts the existing FastAPI entrypoint. Run these commands from `backend/`.

## Deployment

The repository-root `render.yaml` sets `rootDir: backend` and defines the Render web service and managed PostgreSQL database. Its build command trains the synthetic Isolation Forest offline; the API does not train at startup or while handling requests. Configure API, analyst-session and analyst-credential secrets in Render. Configure allowed browser origins with `CORS_ORIGINS`. HTTPS is provided by Render's service endpoint. The MVP includes a per-process IP rate limit, but it is not a distributed limiter or multi-user role system.

## Analyst sign-in

The frontend signs in through `POST /v1/auth/login`. Configure `ANALYST_EMAIL`, `ANALYST_PASSWORD_HASH`, and a randomly generated `SESSION_SIGNING_SECRET` of at least 32 characters in the backend environment. Create a password hash with `python scripts/hash_analyst_password.py`; on Windows without Python, run `scripts\hash_analyst_password.cmd` from Command Prompt. Store only the printed PBKDF2-SHA256 hash in the environment. Generate the signing secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. The API issues an HMAC-signed bearer session that expires after eight hours. `GET /v1/auth/session` validates it. Sign-out clears the browser-held session; sessions expire at the API after the configured lifetime. Existing `X-API-Key` access remains available for backend integrations.

The authenticated frontend also uses `GET /v1/transactions`, `GET /v1/audit`, and the existing case and metrics routes. CORS must allow the deployed frontend origin via `CORS_ORIGINS`. Set the frontend build variable `NEXT_PUBLIC_API_BASE_URL` to the backend origin. Do not set an API key in the frontend.

## Prototype scoring assumptions

Risk bands retain LOW 0–29, MODERATE through the selected validation threshold, ELEVATED through 79, HIGH 80–89, and CRITICAL 90–100. The selected threshold is constrained to 55–65 and is stored with the artifact. When ML is unavailable, rules-only fallback uses the default 60 boundary and configured weights. `RULE_WEIGHTS_JSON` controls individual rule contributions, and `RULE_SCORE_WEIGHT`/`ML_SCORE_WEIGHT` control fallback scoring.
