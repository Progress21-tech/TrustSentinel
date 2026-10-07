# Risk signals and scoring

Signals are deterministic, versioned (`rules_v1`) and derived from account history, beneficiary/device context, and explicit synthetic risk fields. A signal is persisted only when triggered; its evidence is returned in the API response and transaction detail.

| Signal | Trigger | Weight |
|---|---|---:|
| NEW_BENEFICIARY | No prior transaction for this beneficiary on the account | 20 |
| UNUSUAL_AMOUNT | Amount is at least 4x the account's historical average | 20 |
| NEW_DEVICE | No prior transaction for this device on the account | 15 |
| RECENT_ACCOUNT_RECOVERY | Recovery occurred in the previous seven days | 15 |
| HIGH_VELOCITY | At least 3 transactions in 30m or 8 in 24h | 10 |
| BENEFICIARY_RISK | Synthetic beneficiary risk score is at least 60 | 15 |
| NETWORK_RISK | Synthetic network score is at least 60 | 10 |
| BEHAVIOURAL_DEVIATION | Synthetic session anomaly score is at least 0.75 | 10 |

When a model artifact is loaded, a normalized `ml_score` of at least 0.75 also adds a `ML_ANOMALY` evidence record with weight 0. It does not change the rule score because its contribution is already represented by the configured hybrid formula.

Rule points are summed and capped at 100. If an Isolation Forest is available, final score uses the configured rule and ML weights (defaults 0.70 and 0.30), normalized by their sum and clamped to 0–100. Per-signal weights can be overridden with `RULE_WEIGHTS_JSON`. The normalized anomaly score is calibrated as `1 - empirical_percentile(decision_function(raw_features))` against sorted train-normal scores; lower raw scores are more anomalous. The result is bounded to [0,1]. A `ML_ANOMALY` evidence record is added only when the score reaches the configurable 95th percentile tail by default; it has zero rule weight because its contribution is already in the hybrid formula. If unavailable, `ml_score` is null and `ml_status` explicitly reports unavailability; the rules-only score is used when `RULES_ONLY_FALLBACK=true`.

Bands are LOW 0–29, MODERATE 30–59, ELEVATED 60–79, HIGH 80–89, CRITICAL 90–100. Their initial corresponding recommendations are ALLOW, WARN, STEP_UP, HOLD, REVIEW. These weights, thresholds, and actions are prototype assumptions, not calibrated production policy.

## Scenario-target mismatch

The PRD's sample weights and band cutoffs do not produce all its expected scenario bands. New device plus unusual amount yields 35 rule points, below HIGH; recovery, new beneficiary, and unusual amount yield 55, below CRITICAL. With ML's maximum 30-point contribution, the latter still cannot reach CRITICAL. Current results preserve the specified scoring formula and report this mismatch for calibration rather than fabricating signal evidence.
