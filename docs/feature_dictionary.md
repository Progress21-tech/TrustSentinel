# Feature dictionary

All fields are computed from synthetic transaction/account context in the MVP. They are prototype proxies, not private-message, emotion, or intent measurements. Historical values use prior transactions for the same account, before the evaluated transaction timestamp. Numeric ranges below are implementation ranges unless noted.

| Name | Definition and calculation | Type / range | Source | Risk relevance / false-positive behaviour | Privacy |
|---|---|---|---|---|---|
| amount | Current payment amount | number > 0 | Request | Context for deviation; high-value legitimate payments exist | Financial attribute; minimize retention |
| log_amount | `log(1 + amount)` | number ≥ 0 | Derived | Stabilizes amount scale for ML | Derived financial attribute |
| transaction_hour / transaction_day | Hour 0–23 and weekday 0–6 at event time | integer | Timestamp | Off-pattern times may matter; schedules vary | Time context; coarse where possible |
| average_transaction_amount | Mean of up to 500 preceding account payments | number ≥ 0 | Transaction history | Baseline; business profile changes can shift it | Historical financial behaviour |
| median_transaction_amount | Median of up to 500 preceding payments | number ≥ 0 | Transaction history | Robust baseline; legitimate one-offs differ | Historical financial behaviour |
| max_transaction_amount | Maximum of up to 500 preceding payments | number ≥ 0 | Transaction history | Context only; old extremes may be stale | Historical financial behaviour |
| transaction_count_30m / transaction_count_24h | Prior account payments in rolling windows | integer ≥ 0 | Transaction history | Velocity; batch/business activity can be normal | Activity metadata |
| average_daily_transactions | Historical count divided by account age in days | number ≥ 0 | Transactions/account | Behaviour baseline; sparse accounts are noisy | Activity metadata |
| amount_deviation_ratio | Current amount / historical mean (1 when no history); capped at 1000 | number ≥ 0 | Request + history | High ratio can be legitimate; never use alone | Derived financial behaviour |
| time_of_day_deviation | Placeholder score for deviation from account time baseline | 0 in MVP | Synthetic context | Not yet a signal; should not be used as evidence | No private activity is collected |
| is_new_beneficiary | No prior account transaction with beneficiary | boolean | Transaction history | Can indicate unfamiliar destination; new legitimate payees occur | Pseudonymous beneficiary ID |
| beneficiary_age_days | Days since synthetic beneficiary first seen (0 if absent) | integer ≥ 0 | Beneficiary record | Newness context; global age differs from account familiarity | Pseudonymous metadata |
| beneficiary_risk_score | Synthetic beneficiary score | 0–100 | Beneficiary record | Network/reputation proxy; errors can affect innocent recipients | Synthetic-only in MVP |
| beneficiary_transaction_count | Prior transactions to this beneficiary | integer ≥ 0 | Transaction history | Familiarity context; low count is not proof of risk | Financial history |
| unique_beneficiary_count | Distinct prior beneficiaries | integer ≥ 0 | Transaction history | Changing payees can be unusual; business accounts differ | Financial history |
| is_new_device | No prior account transaction from device | boolean | Transaction history | New access context; upgrades/travel create false positives | Pseudonymous device ID |
| device_age_days | Days since device first seen (0 if absent) | integer ≥ 0 | Device record | Device familiarity context | Pseudonymous metadata |
| recent_device_change | Account device change within 7 days | boolean | Account record | Recovery/upgrade may be legitimate | Security event metadata |
| device_risk_flag | Device has synthetic risk flags | boolean | Device record | Supports network context; synthetic only | No raw fingerprint stored |
| account_age_days | Days since account creation | integer ≥ 0 | Account record | New accounts may have less history | Account metadata |
| recent_account_recovery | Recovery within previous 7 days | boolean | Account record | Recovery plus payment context may raise risk | Security event metadata |
| recent_password_reset / recent_pin_reset | Placeholder reset context | boolean, false in MVP | Synthetic context | Not implemented as live signals | Never collect credentials or PIN values |
| session_duration_deviation | Placeholder synthetic session proxy | 0 in MVP | Synthetic context | Not used in MVP | No communications or biometrics |
| interaction_velocity | Placeholder synthetic interaction proxy | 0 in MVP | Synthetic context | Not used in MVP | No keystrokes collected |
| navigation_deviation_score | Placeholder synthetic navigation proxy | 0 in MVP | Synthetic context | Not used in MVP | No browsing history collected |
| session_anomaly_score | Synthetic session proxy; 0 unless supplied by controlled data | 0–1 | Synthetic context | Signal threshold 0.75; not an emotional-state claim | Synthetic-only |
| linked_risky_accounts / linked_risky_devices / linked_risky_beneficiaries | Counts of synthetic risky links | integer ≥ 0 | Synthetic graph context | Relationship evidence can be noisy | Synthetic-only; no cross-bank sharing |
| beneficiary_in_degree / beneficiary_out_degree | Synthetic incoming/outgoing relationship counts | integer ≥ 0, 0 in MVP | Synthetic network | Network concentration context; unused until graph data exists | Synthetic-only |
| network_risk_score | MVP uses beneficiary risk score as network proxy | 0–100 | Beneficiary record | Proxy can create false positives; synthetic only | No real network intelligence |
