# TrustSentinel fresh synthetic evaluation data

- Generated: 2026-10-08; seed: 20261008; records: 1000.
- Feature schema: trustsentinel-context-v1.
- Synthetic identifiers and values; generated independently of prior datasets.
- Not used for training or calibration; those scripts read only data/synthetic/transactions.csv.
- Feature columns are request context inputs grouped in the API context_features property. scenario_category and ground_truth_label are offline-only; exclude them from API/model input.

| Category | Count |
|---|---:|
| normal | 500 |
| legitimate_high_value | 100 |
| borderline_unusual | 100 |
| new_beneficiary_abnormal_amount | 70 |
| new_device_high_value | 60 |
| rapid_transfers_new_beneficiary | 60 |
| risky_beneficiary_network | 40 |
| account_recovery_new_beneficiary | 40 |
| combined_high_risk | 30 |

| transaction_id | account_id | amount | channel | scenario_category | ground_truth_label |
|---|---|---:|---|---|---:|
| FRESH-20261008-0000 | FACC-20261008-0000 | 137682.13 | web | normal | 0 |
| FRESH-20261008-0001 | FACC-20261008-0001 | 6082309.13 | web | legitimate_high_value | 0 |
| FRESH-20261008-0002 | FACC-20261008-0002 | 89638.77 | web | normal | 0 |
| FRESH-20261008-0003 | FACC-20261008-0003 | 197917.36 | ussd | normal | 0 |
| FRESH-20261008-0004 | FACC-20261008-0004 | 248919.24 | mobile_app | normal | 0 |
| FRESH-20261008-0005 | FACC-20261008-0005 | 46157.29 | api | new_device_high_value | 1 |
| FRESH-20261008-0006 | FACC-20261008-0006 | 150685.07 | web | normal | 0 |
| FRESH-20261008-0007 | FACC-20261008-0007 | 110353.74 | mobile_app | normal | 0 |
| FRESH-20261008-0008 | FACC-20261008-0008 | 145616.18 | api | normal | 0 |
| FRESH-20261008-0009 | FACC-20261008-0009 | 110847.39 | web | normal | 0 |
| FRESH-20261008-0010 | FACC-20261008-0010 | 6199264.25 | api | legitimate_high_value | 0 |
| FRESH-20261008-0011 | FACC-20261008-0011 | 4095457.18 | ussd | legitimate_high_value | 0 |
