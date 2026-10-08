# API reference

FastAPI generates the full OpenAPI schema at `/openapi.json` and interactive docs at `/docs`.

## Score a transaction

Protected routes accept the signed analyst bearer session issued by `POST /v1/auth/login`. Existing integrations may continue using `X-API-Key` when `API_KEY_SECRET` is configured. In production, protected routes fail closed if neither credential mechanism is configured.

- `POST /v1/auth/login` verifies configured analyst credentials and issues an eight-hour signed session
- `GET /v1/auth/session` validates the bearer session
- `POST /v1/risk/score`

Required JSON fields: `transaction_id`, `account_id`, positive `amount`, `beneficiary_id`, `device_id`, and `channel` (`mobile_app`, `web`, `ussd`, `api`). `currency` defaults to NGN; `timestamp` defaults to server UTC time. Requesters provide raw event/context identifiers, never precomputed scores. Account must exist. Duplicate transaction IDs are idempotent and return the stored decision.

Response includes `risk_score`, `risk_band`, `recommended_action`, `reason_codes`, `explanation`, `rule_score`, nullable `ml_score`, `ml_status`, version identifiers, measured latency, triggered signal evidence, and optional `case_id`.

## Other endpoints

- `GET /health`, `GET /ready`
- `POST /v1/sandbox/scenario` with one of the eight stable scenario names
- `GET /v1/transactions/{transaction_id}`
- `GET /v1/transactions?limit=50`
- `GET /v1/audit?limit=100`
- `GET /v1/cases?status=&risk_band=&date=YYYY-MM-DD&outcome=`
- `GET /v1/cases/{case_id}`
- `POST /v1/cases/{case_id}/outcome` with `outcome`, optional `notes`, and `analyst_id`
- `GET /v1/metrics/summary`

Errors use `{ "error": { "code": "...", "message": "..." } }`. Validation failures return 422, unknown records return 404, duplicate/invalid lifecycle conflicts return 409, invalid sandbox keys return 401, and unexpected failures return a generic 500 without stack traces.
