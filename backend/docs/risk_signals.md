# Risk signals and scoring

Signals are deterministic and versioned (`rules_v1`). The six rules below use
account transaction history and the stored beneficiary risk score. A signal is
persisted only when triggered; its evidence is returned by the API.

| Signal | Trigger | Weight |
|---|---|---:|
| NEW_BENEFICIARY | No prior transaction for this beneficiary on the account | 20 |
| UNUSUAL_AMOUNT | Amount is at least 4x the account's historical average | 20 |
| NEW_DEVICE | No prior transaction for this device on the account | 15 |
| RECENT_ACCOUNT_RECOVERY | Recovery occurred in the previous seven days | 15 |
| HIGH_VELOCITY | At least 3 transactions in 30m or 8 in 24h | 10 |
| BENEFICIARY_RISK | Stored beneficiary risk score is at least 60 | 15 |

When the model's normalized `ml_score` reaches `ML_ANOMALY_REASON_THRESHOLD`
(default 0.95), the API adds a `ML_ANOMALY` evidence record with zero rule
weight. The ML contribution is already included by the hybrid formula.

Rule points are summed and capped at 100. If ML is available, the artifact's
validation-selected weights combine the rules score and normalized anomaly
score into a 0–100 hybrid score. The selected high-risk threshold (limited to
55–65) sets the MODERATE/ELEVATED boundary; LOW remains 0–29, ELEVATED extends
through 79, HIGH is 80–89, and CRITICAL is 90–100. Recommendations are ALLOW,
WARN, STEP_UP, HOLD, and REVIEW respectively. These are prototype assumptions,
not real-world fraud policy.

If ML is unavailable, `ml_score` is null and `ml_status` reports
`unavailable_rules_only`; the rules-only score is used when
`RULES_ONLY_FALLBACK=true`. Session and graph proxy rules were removed because
the serving system has no equivalent live measurements. Synthetic evaluation
reports scenario-level metrics and legitimate-scenario false-positive rates;
they are not evidence of real-world fraud performance.
