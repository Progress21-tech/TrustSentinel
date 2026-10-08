# Train/serving alignment decision

Stage 3 identified that v1 included synthetic session and graph values that had
no live measurement, and that several history values were fabricated instead
of derived from transaction history. It also identified the ambiguity of a
cold-start amount ratio of 1.

Stage 4 implements a new feature contract, `trustsentinel-context-v2`, in
[`app/ml/features.py`](../app/ml/features.py) and routes both the synthetic
generator and live extractor through `extract_feature_context`. The v2 feature
definitions, inputs, ranges, missing-value behavior, and excluded v1 fields are
documented in [`feature_dictionary.md`](feature_dictionary.md).

The v2 schema adds `has_account_history`, removes unavailable session and graph
proxies, derives history-dependent values from prior events, and treats a
history-free amount ratio as 1 only when the availability flag is 0. This is a
material schema change; it requires the new versioned v2 artifact. The existing
v1 artifact is neither overwritten nor compatible with the v2 schema.

## Validation and deployment boundary

The Stage 4 pipeline is implemented, but has not been run in this workspace.
There is no usable Python runtime, so no v2 dataset, calibration selection,
trained artifact, validation experiment report, or held-out evaluation has
been generated here. The held-out test must not be used to select model or
policy settings. The v1 deployed artifact is not present in the local
checkout, so an old-model score comparison on the v2 held-out set is
unavailable unless the authorized v1 artifact is separately obtained.

No production deployment has occurred. The currently deployed service remains
unchanged until a new deployment is deliberately made after validation and
final evaluation.
