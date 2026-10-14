# Synthetic evaluation status

No current evaluation report is committed or generated in this checkout. The model artifact and generated data are absent, and Windows denied execution of the available Python binary here; therefore no metric is reported.

The repository evaluator at scripts/evaluate_model.py requires a calibrated artifact and matching deterministic dataset hash. It expects account-disjoint train/validation/test splits with a held-out 2,000-row test set and reports proxy metrics for synthetic labels. These labels are generator assumptions, not observed bank fraud outcomes. Do not describe a result as real-world precision, fraud probability, loss reduction or payment prevention.

To generate a reproducible report from backend/ in a supported environment:

    python scripts/generate_data.py
    python scripts/calibrate_policy.py
    python scripts/train_model.py
    python scripts/validation_experiments.py
    python scripts/evaluate_model.py

Archive artifact metadata, dataset hash, seed, split counts, report and code revision together. Evaluate cold-start and legitimate high-value scenarios. Do not tune thresholds on held-out test data. Report metrics only after checking the generated report.

Status: NOT RUN. No metrics or conclusions are inferred from scripts alone.
