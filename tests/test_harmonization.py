import pandas as pd
import pytest

from labor_market_analysis.config import TARGET_COLUMNS
from labor_market_analysis.harmonization import harmonize_dataframe


def test_harmonizes_uppercase_schema_and_filters_age(source_frame: pd.DataFrame) -> None:
    result = harmonize_dataframe(source_frame)

    assert list(result.columns) == list(TARGET_COLUMNS)
    assert len(result) == 3
    assert result["region"].tolist() == [45, 3, 11]
    assert result["gender"].tolist() == ["male", "female", "male"]
    assert result["labor_force_status"].tolist() == [
        "employed",
        "unemployed",
        "not_in_labor_force",
    ]
    assert result["age_5group"].tolist() == ["30-34", "20-24", "50-54"]


def test_harmonizes_lowercase_source_names(source_frame: pd.DataFrame) -> None:
    lower = source_frame.rename(columns=str.lower)
    result = harmonize_dataframe(lower)

    assert len(result) == 3
    assert result.loc[0, "year"] == 2023


def test_rejects_missing_critical_column(source_frame: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="required fields"):
        harmonize_dataframe(source_frame.drop(columns="VESA"))


def test_rejects_negative_weight(source_frame: pd.DataFrame) -> None:
    source_frame.loc[0, "VESA"] = -1
    with pytest.raises(ValueError, match="negative weights"):
        harmonize_dataframe(source_frame)
