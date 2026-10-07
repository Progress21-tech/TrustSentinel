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
python scripts/train_model.py
python scripts/evaluate_model.py
```

Generation is seeded and writes linked entities plus at least 10,000 transactions under `data/synthetic/`. The database seed is idempotent and skips a non-empty customer database. Train the Isolation Forest offline; the API never trains during startup or requests. The generated artifact is ignored by Git. Until an artifact exists or if loading/inference fails, scoring explicitly returns `ml_status: unavailable_rules_only` and uses the rules-only score.

### ML scoring details

The model is an **Isolation Forest**, a lightweight unsupervised anomaly detector suited to a synthetic prototype where labelled examples are limited. It learns only background rows from the reproducible training split. Scenario names, split markers, and labels are never features. The persisted sklearn pipeline applies `StandardScaler` before Isolation Forest inference.

The canonical feature builder is [`app/ml/features.py`](app/ml/features.py), used by synthetic generation, training, evaluation, and live feature extraction. The ordered feature schema (`trustsentinel-context-v1`) includes log amount and amount deviation, transaction hour and time deviation, 30m/24h velocity, beneficiary age/risk/history, device age/newness/change, recent recovery/reset flags, synthetic session proxies, linked-risk counts, beneficiary network degrees/risk, account age, and average daily activity. Values are numeric, finite, bounded where appropriate, and missing fields have explicit defaults.

Training uses the normal/background portion of the train split and a fixed random seed. Defaults are 200 estimators, `max_samples=auto`, `contamination=auto`, and `max_features=1.0`; `ML_N_ESTIMATORS`, `ML_RANDOM_STATE`, `ML_MAX_SAMPLES`, `ML_CONTAMINATION`, and `ML_MAX_FEATURES` configure the prototype. The model is written to `models/isolation_forest_v1.joblib` (or `MODEL_PATH`), tagged `iforest-v1.0.0`, and includes the dataset seed/version, exact feature ordering/version, training configuration, and calibration reference. The model is generated during setup/deployment build rather than committed.

Isolation Forest's raw `decision_function` is calibrated against sorted scores from the train-normal rows: `ml_score = 1 - empirical_percentile(raw_score)`. Lower raw scores are more anomalous, so the resulting risk contribution is deterministic and bounded to `[0, 1]`; values at or below the training reference minimum approach 1.0. With default weights, `hybrid_score = 0.70 * rule_score + 0.30 * (ml_score * 100)`, clamped to 0–100. Configured weights are normalized by their sum. The ML score does not set the action directly; the existing risk-band policy does.

If the artifact is missing, incompatible, or inference fails, the API explicitly returns `ml_score: null`, `ml_status: unavailable_rules_only`, and `model_version: rules-only` when `RULES_ONLY_FALLBACK=true`. With fallback disabled, scoring returns 503. When active, the response includes the loaded model version and `feature_schema_version`. `ML_ANOMALY_REASON_THRESHOLD` controls when the calibrated tail is recorded as an evidence signal; the model never creates free-form explanations.

Run `python scripts/evaluate_model.py` after training to compare **rules-only**, **ML-only**, and **hybrid** predictions on the same held-out synthetic set. It prints sample counts, precision/recall/F1 and false-positive proxies, confusion counts, per-scenario scores, scenario coverage, and model inference latency; it writes `data/generated/evaluation_report.json`. It also runs the deterministic scenarios through the same risk service and checks stored decisions, signals, cases, and audit events. Two legitimate high-value variations are included in the evaluation dataset.

The supplied GitHub Actions report records a baseline for 2,000 held-out synthetic rows: hybrid precision proxy 89.56%, recall proxy 32.21%, F1 proxy 47.38%, and false-positive proxy 1.27%. Rules-only and ML-only comparisons, per-scenario rates, live demo results, and limits of that aggregate report are summarized in [`docs/calibration_baseline.md`](docs/calibration_baseline.md). These results are synthetic proxies and are not evidence of production fraud-detection accuracy on Nigerian financial institution data. The held-out report is baseline evidence only; do not use it to tune a final model configuration.

Known data limitation: the synthetic generator can include session and network context, while the current live extractor has only partial session/network context and supplies documented defaults for fields it cannot observe. This can create train/live feature shift. Validate those fields against real, approved backend signals before using model scores beyond this prototype.

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

The repository-root `render.yaml` sets `rootDir: backend` and defines the Render web service and managed PostgreSQL database. Its build command trains the synthetic Isolation Forest offline; the API does not train at startup or while handling requests. Set `API_KEY_SECRET` in Render. Configure allowed browser origins with `CORS_ORIGINS`. HTTPS is provided by Render's service endpoint. The MVP includes a per-process IP rate limit, but it is not a distributed limiter. It does not implement user login or role-based dashboard access.

## Prototype scoring assumptions

Risk bands follow the PRD thresholds: LOW 0–29, MODERATE 30–59, ELEVATED 60–79, HIGH 80–89, CRITICAL 90–100. Rule weights and the 70/30 rules/ML hybrid formula are documented prototype assumptions. Several expected demo bands in the PRD are unreachable for the listed signals under those weights: new beneficiary + unusual amount yields 40 points (at most 58 with an ML score of 1); new device + unusual amount yields 35 (below HIGH); recovery + new beneficiary + unusual amount yields 55 (at most 68 with an ML score of 1); rapid transfers and risky beneficiary also remain below HIGH without further evidence. The implementation preserves the explicit weights and thresholds and exposes the actual signals and score. Adjust weights using `RULE_WEIGHTS_JSON`, `RULE_SCORE_WEIGHT`, and `ML_SCORE_WEIGHT` when calibrating the demo policy.
