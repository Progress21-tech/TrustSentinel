# Calibration baseline

Source: the supplied GitHub Actions `evaluation_report.json`, dataset `trustsentinel-synthetic-v1-seed-2026`, feature schema `trustsentinel-context-v1`, model `iforest-v1.0.0`. The report covers 2,000 held-out synthetic records: 1,494 normal and 506 labelled high-risk. These are synthetic proxies, not real-world fraud performance.

## Held-out baseline

| Method | Precision proxy | Recall proxy | F1 proxy | False-positive proxy |
| --- | ---: | ---: | ---: | ---: |
| Rules only | 97.96% | 9.49% | 17.30% | 0.07% |
| ML only | 74.27% | 85.57% | 79.52% | 10.04% |
| Hybrid, 70/30, threshold 60 | 89.56% | 32.21% | 47.38% | 1.27% |

The hybrid misses the stated prototype precision goal (>90%) by 0.44 percentage points, while its reported false-positive proxy is below 10%. The rules-only result has higher precision and very low false positives but misses most positive examples. ML-only has higher recall and F1, with lower precision and a false-positive proxy slightly above 10%.

## Scenario score evidence

| Scenario | Median rules | Median ML (0–100) | Median hybrid | Hybrid high-risk rate |
| --- | ---: | ---: | ---: | ---: |
| Normal | 0.00 | 39.97 | 11.99 | 0% |
| Borderline | 20.00 | 89.14 | 39.50 | 6.51% |
| Legitimate high value | 0.00 | 70.64 | 21.19 | 0% |
| Legitimate business high value | 0.00 | 79.70 | 23.91 | 0% |
| Account recovery + new beneficiary | 55.00 | 92.63 | 66.13 | 72.88% |
| Combined high risk | 100.00 | 100.00 | 100.00 | 100% |
| New beneficiary + abnormal amount | 40.00 | 94.97 | 56.90 | 37.96% |
| New device + high value | 35.00 | 98.19 | 54.03 | 25% |
| Rapid transfers + new beneficiary | 30.00 | 93.78 | 49.13 | 0% |
| Risky beneficiary network | 25.00 | 82.76 | 43.02 | 0% |

These results show that high anomaly scores do not alone cross the hybrid high-risk threshold. At 70/30, the median hybrid scores for rapid transfers and risky-beneficiary network remain below 60 despite elevated median ML contributions. The high ML medians for borderline and legitimate unusual-value groups also show that Isolation Forest rarity is not equivalent to scam likelihood. Normal and both legitimate high-value groups nevertheless had a 0% high-risk rate in this held-out report.

## Live versus offline discrepancy to investigate

The report’s live demo gives ML scores of approximately 0.935 for `normal` and 0.953 for `legitimate_high_value`, while the held-out synthetic medians are 0.400 and 0.706 respectively. This indicates a material difference between these particular live demo vectors and the held-out scenario groups; it does not establish the cause.

The source confirms representation differences worth measuring: synthetic generation varies session proxies and beneficiary network-degree values, while live extraction sets session proxies and beneficiary degree values to zero. Synthetic generation also varies time-of-day deviation while live extraction supplies zero. Other graph indicators are only partially represented in live extraction. The supplied aggregate report has no raw `decision_function` values or per-feature distributions, so it cannot establish how much these differences contribute.

## Calibration status

The prior “calibration pass” commit changed documentation only; it did not change hyperparameters, weights, calibration, thresholds, or the persisted model. The new report repeats the same held-out counts and classification metrics; its latency and generated case identifier differ, as expected for runtime/random values.

The repository now contains `scripts/calibrate_policy.py`. It reserves the same every-fifth 2,000 test rows, assigns one fifth of the former training rows to validation, and fits candidates on train-normal rows. It reports thresholds 55–65 and the 80/20 through 60/40 weight candidates; it tests the existing empirical-rank calibration and training-normal-tail excess calibration at train-derived 80th, 90th, and 95th percentile cutoffs. Selection is validation-only, preserves zero high-risk rates for normal and both legitimate scenarios, requires false-positive rate below 10%, prefers candidates above 90% precision, and fixes the deployed boundary at 60 to preserve the existing risk bands. Among target-meeting candidates it prefers the smallest policy/calibration change when validation recall and F1 do not regress; otherwise it chooses the best validation F1 among safe candidates and reports whether the precision target was missed.

The script writes `data/generated/calibration_validation_report.json` and `calibration_selection.json`. Training persists the selected calibration and weights in the artifact, and online inference reads them from that artifact. Evaluation reports the retrained old-policy comparator and selected policy on the untouched held-out split, plus the deterministic API scenario runs. The workflow, Docker build, and Render build sequence now runs calibration before training. These new experiments have **not run yet** in this checkout: the generated dataset/model are absent and Python is unavailable. No selected settings or final held-out result are claimed here.
