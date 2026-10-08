# Feature contract: `trustsentinel-context-v2`

This is the canonical ordered model-input contract implemented in
[`app/ml/features.py`](../app/ml/features.py). The online service and synthetic
generator call the same `extract_feature_context` function. Training labels,
scenario names, IDs, currency, and channel are not model features.

The generator models event histories and entity state. It does not draw the
final feature values independently. It runs those histories through the same
extractor used by serving. All times are timezone-aware UTC. Missing numeric
measurements become zero except `amount_deviation_ratio`, whose cold-start
fallback is 1 and is paired with `has_account_history=0`.

| # | Feature | Meaning and source | Transformation / type / valid range | Missing and cold-start behavior |
|---:|---|---|---|---|
| 1 | `log_amount` | Current transaction amount from request | `log1p(amount)`; float, [0, log1p(1e9)] | Missing/invalid amount becomes 0 before transform |
| 2 | `amount_deviation_ratio` | Current amount divided by mean of up to 500 prior account transactions | Float, [0,1000], capped | No prior transaction: 1. Distinguish this from measured ratio 1 using `has_account_history` |
| 3 | `has_account_history` | Whether at least one earlier transaction exists for this account | Boolean encoded 0/1 | 0 for a new or history-free account |
| 4 | `transaction_hour` | UTC hour of the transaction timestamp | Integer-valued float, [0,23] | Missing/invalid timestamp falls back to current UTC time in extraction |
| 5 | `transaction_count_30m` | Prior account transactions in the 30 minutes before this event | Count, [0,100000] | 0 when no qualifying history exists |
| 6 | `transaction_count_24h` | Prior account transactions in the 24 hours before this event | Count, [0,100000] | 0 when no qualifying history exists |
| 7 | `beneficiary_age_days` | Days since beneficiary entity `first_seen_at` | Nonnegative integer-valued float, capped at 100000 | 0 if beneficiary record is unavailable or first seen at event time |
| 8 | `beneficiary_risk_score` | Persisted beneficiary risk score | Float, [0,100] | 0 when no score/beneficiary record is available |
| 9 | `beneficiary_transaction_count` | Prior transactions from this account to this beneficiary | Count, [0,100000] | 0 for a beneficiary unused by this account |
| 10 | `unique_beneficiary_count` | Distinct beneficiaries in prior account transaction history | Count, [0,100000] | 0 for an account with no history |
| 11 | `is_new_beneficiary` | No prior account transaction to the beneficiary | Boolean encoded 0/1 | 1 for an unseen account-beneficiary pair |
| 12 | `device_age_days` | Days since this account/device record `first_seen_at` | Nonnegative integer-valued float, capped at 100000 | 0 when the device record is absent or first seen at event time |
| 13 | `is_new_device` | No prior account transaction from this device | Boolean encoded 0/1 | 1 for an unseen account-device pair |
| 14 | `recent_device_change` | Account `last_device_change_at` falls in the preceding seven days | Boolean encoded 0/1 | 0 when no qualifying device-change event is recorded |
| 15 | `recent_account_recovery` | Account `last_recovery_at` falls in the preceding seven days | Boolean encoded 0/1 | 0 when no qualifying recovery event is recorded |
| 16 | `account_age_days` | Days since account `created_at` | Nonnegative integer-valued float, capped at 100000 | 0 if account creation time is unavailable or equals event time |
| 17 | `average_daily_transactions` | Prior transaction count divided by account age in days plus one | Float, [0,100000] | 0 for a history-free account |

The feature matrix is ordered exactly as the table. The fitted pipeline applies
`StandardScaler` followed by `IsolationForest`; the scaler and model are stored
together in the versioned artifact. The public scoring API accepts transaction
facts, not caller-supplied model feature values.

## Excluded from v2

The following v1 fields were removed because training fabricated values that
serving could not measure, or because they duplicated another feature without
independent evidence:

- Session/time proxies: `time_of_day_deviation`, `session_duration_deviation`,
  `interaction_velocity`, `navigation_deviation_score`, and
  `session_anomaly_score`.
- Reset placeholders: `recent_password_reset` and `recent_pin_reset` (constant
  false with no event source).
- Synthetic graph values: `linked_risky_accounts`, `linked_risky_devices`,
  `linked_risky_beneficiaries`, `beneficiary_in_degree`, and
  `beneficiary_out_degree`.
- Redundant proxy: `network_risk_score`, which duplicated beneficiary risk
  score rather than measuring an independent network signal.

Network risk is represented only by the persisted beneficiary risk score until
TrustSentinel has a documented graph source available both during training and
live scoring. Session fields remain excluded until scoring-time telemetry has
a defensible source and matching training representation.

## Dataset construction and leakage controls

Synthetic v2 creates 10,000 transactions for 1,000 accounts. Each account is
assigned wholly to one split: 600 accounts / 6,000 events for training, 200 /
2,000 for validation, and 200 / 2,000 for held-out testing. History-derived
features use only events strictly before the scored event. Validation selects
calibration and policy; held-out records are reserved for the final evaluation.
The split schema is `account_disjoint_train_validation_test_v2`; the fixed
default generation seed is 2026.

`synthetic_label`, `evaluation_scenario`, `dataset_split`, and
`dataset_seed` are evaluation metadata. `build_ml_features` selects only the
named features above and ignores these metadata columns. The target is a
synthetic scenario proxy and must not be described as real-world fraud accuracy.
