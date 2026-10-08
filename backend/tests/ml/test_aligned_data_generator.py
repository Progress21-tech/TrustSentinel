import pandas as pd

from app.ml.features import FEATURES, FEATURE_SCHEMA_VERSION
from scripts.generate_data import generate


def test_generator_uses_history_features_and_account_disjoint_splits(tmp_path):
    first = generate(seed=17, output=tmp_path / "first", transactions=100)
    second = generate(seed=17, output=tmp_path / "second", transactions=100)
    rows = pd.read_csv(first / "transactions.csv")
    repeat = pd.read_csv(second / "transactions.csv")

    assert len(rows) == 100
    assert rows.dataset_split.value_counts().to_dict() == {"train": 60, "validation": 20, "test": 20}
    assert rows.groupby("account_id").dataset_split.nunique().max() == 1
    assert set(FEATURES).issubset(rows.columns)
    assert set(rows.feature_schema_version) == {FEATURE_SCHEMA_VERSION}
    assert set(rows.dataset_version) == {"trustsentinel-synthetic-v2"}
    assert not {"synthetic_label", "evaluation_scenario", "dataset_split"}.intersection(FEATURES)
    assert rows["has_account_history"].isin([0, 1]).all()
    assert rows.loc[rows.has_account_history == 0, "amount_deviation_ratio"].eq(1).all()
    assert first.joinpath("transactions.csv").read_bytes() == second.joinpath("transactions.csv").read_bytes()
