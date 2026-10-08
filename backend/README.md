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
python scripts/evaluate_model.py
```

Generation is seeded and writes linked entities plus at least 10,000 transactions under `data/synthetic/`. The database seed is idempotent and skips a non-empty customer database. Train the Isolation Forest offline; the API never trains during startup or requests. The generated artifact is ignored by Git. Until an artifact exists or if loading/inference fails, scoring explicitly returns `ml_status: unavailable_rules_only` and uses the rules-only score.

### ML scoring details

The model is an **Isolation Forest**, a lightweight unsupervised anomaly detector suited to a synthetic prototype where labelled examples are limited. It learns only background rows from the reproducible training split. Scenario names, split markers, and labels are never features. The persisted sklearn pipeline applies `StandardScaler` before Isolation Forest inference.

The canonical feature builder is [`app/ml/features.py`](app/ml/features.py), used by synthetic generation, training, evaluation, and live feature extraction. The ordered feature schema (`trustsentinel-context-v1`) includes log amount and amount deviation, transaction hour and time deviation, 30m/24h velocity, beneficiary age/risk/history, device age/newness/change, recent recovery/reset flags, synthetic session proxies, linked-risk counts, beneficiary network degrees/risk, account age, and average daily activity. Values are numeric, finite, bounded where appropriate, and missing fields have explicit defaults.

Training uses only the normal/background portion of the train split and a fixed random seed. Defaults remain 200 estimators, `max_samples=auto`, `contamination=auto`, and `max_features=1.0`; `ML_N_ESTIMATORS`, `ML_RANDOM_STATE`, `ML_MAX_SAMPLES`, `ML_CONTAMINATION`, and `ML_MAX_FEATURES` configure the prototype. The model is written to `models/isolation_forest_v1.joblib` (or `MODEL_PATH`) and records the dataset/split version, exact feature schema, training configuration, calibration method/cutoff, and selected policy. The artifact model version defaults to `iforest-v1.1.0`; the validated hybrid policy is versioned separately. Artifacts are generated during setup/deployment build rather than committed.

Isolation Forest's raw `decision_function` is calibrated against sorted scores from the train-normal rows. The legacy mapping is `ml_score = 1 - empirical_percentile(raw_score)`. Validation may select a monotonic training-normal-tail excess mapping instead; its method and cutoff are persisted in the model artifact. Both produce a bounded contribution in `[0, 1]`. The legacy hybrid formula is `0.70 * rule_score + 0.30 * (ml_score * 100)`, clamped to 0–100. After validation calibration, the artifact stores and the API uses the selected rules/ML weights; rules-only fallback continues using configured weights. The ML score does not set the action directly; the existing risk-band policy does.

If the artifact is missing, incompatible, or inference fails, the API explicitly returns `ml_score: null`, `ml_status: unavailable_rules_only`, and `model_version: rules-only` when `RULES_ONLY_FALLBACK=true`. With fallback disabled, scoring returns 503. When active, the response includes the loaded model version and `feature_schema_version`. `ML_ANOMALY_REASON_THRESHOLD` controls when the calibrated tail is recorded as an evidence signal; the model never creates free-form explanations.

Run `python scripts/evaluate_model.py` after training to compare **rules-only**, **ML-only**, and **hybrid** predictions on the same held-out synthetic set. It prints sample counts, precision/recall/F1 and false-positive proxies, confusion counts, per-scenario scores, scenario coverage, and model inference latency; it writes `data/generated/evaluation_report.json`. It also runs the deterministic scenarios through the same risk service and checks stored decisions, signals, cases, and audit events. Two legitimate high-value variations are included in the evaluation dataset.

The supplied GitHub Actions report records a baseline for 2,000 held-out synthetic rows: hybrid precision proxy 89.56%, recall proxy 32.21%, F1 proxy 47.38%, and false-positive proxy 1.27%. Rules-only and ML-only comparisons, per-scenario rates, live demo results, and limits of that aggregate report are summarized in [`docs/calibration_baseline.md`](docs/calibration_baseline.md). These results are synthetic proxies and are not evidence of production fraud-detection accuracy on Nigerian financial institution data. The held-out report is baseline evidence only; do not use it to tune a final model configuration.

Before training a new artifact, run `python scripts/calibrate_policy.py`. It uses the validation split only to compare the existing empirical-rank calibration against a monotonic training-normal-tail calibration, the requested 55–65 thresholds, and the five rules/ML weight pairs. It preserves the configured high-risk boundary at 60, writes a reproducible policy selection, and enforces normal/legitimate scenario safety. `train_model.py` stores that selection in the model artifact; the API loads its calibration and weights with the model. `evaluate_model.py` then evaluates the unchanged 2,000-row test split once and compares the retrained old policy with the selected policy. Run the full sequence in the order shown above. Artifacts and reports remain under ignored `data/generated/` and `models/` paths.

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

The repository-root `render.yaml` sets `rootDir: backend` and defines the Render web service and managed PostgreSQL database. Its build command trains the synthetic Isolation Forest offline; the API does not train at startup or while handling requests. Configure API, analyst-session and analyst-credential secrets in Render. Configure allowed browser origins with `CORS_ORIGINS`. HTTPS is provided by Render's service endpoint. The MVP includes a per-process IP rate limit, but it is not a distributed limiter or multi-user role system.

## Analyst sign-in

The frontend signs in through `POST /v1/auth/login`. Configure `ANALYST_EMAIL`, `ANALYST_PASSWORD_HASH`, and a randomly generated `SESSION_SIGNING_SECRET` of at least 32 characters in the backend environment. Create a password hash with `python scripts/hash_analyst_password.py`; on Windows without Python, run `scripts\hash_analyst_password.cmd` from Command Prompt. Store only the printed PBKDF2-SHA256 hash in the environment. Generate the signing secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. The API issues an HMAC-signed bearer session that expires after eight hours. `GET /v1/auth/session` validates it. Sign-out clears the browser-held session; sessions expire at the API after the configured lifetime. Existing `X-API-Key` access remains available for backend integrations.

The authenticated frontend also uses `GET /v1/transactions`, `GET /v1/audit`, and the existing case and metrics routes. CORS must allow the deployed frontend origin via `CORS_ORIGINS`. Set the frontend build variable `NEXT_PUBLIC_API_BASE_URL` to the backend origin. Do not set an API key in the frontend.

## Prototype scoring assumptions

Risk bands follow the existing PRD thresholds: LOW 0–29, MODERATE 30–59, ELEVATED 60–79, HIGH 80–89, CRITICAL 90–100. The 70/30 rules/ML combination is the historical baseline and remains the fallback when no selected model policy is available. With a calibrated artifact, the API uses its versioned validation-selected weights while keeping the risk-band boundary at 60. Several expected demo bands in the PRD are unreachable for some listed signal combinations under the configured rule contributions; the engine preserves deterministic signals and graduated interventions instead of hardcoding scenario outcomes. `RULE_WEIGHTS_JSON` controls individual rule contributions, and `RULE_SCORE_WEIGHT`/`ML_SCORE_WEIGHT` control rules-only fallback and the baseline policy.
