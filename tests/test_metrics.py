import pandas as pd
import pytest

from labor_market_analysis.metrics import informal_employment_share, unemployment_rate


def test_unemployment_excludes_people_outside_labor_force(
    harmonized_metrics_frame: pd.DataFrame,
) -> None:
    result = unemployment_rate(
        harmonized_metrics_frame[harmonized_metrics_frame["month"] == 1]
    )

    assert result.loc[0, "unemployment_rate"] == pytest.approx(25.0)
    assert result.loc[0, "weighted_denominator"] == pytest.approx(4.0)
    assert result.loc[0, "unweighted_n"] == 2
    assert 0 <= result.loc[0, "ci_lower"] < result.loc[0, "ci_upper"] <= 100


def test_informal_share_uses_only_employed_respondents(
    harmonized_metrics_frame: pd.DataFrame,
) -> None:
    result = informal_employment_share(harmonized_metrics_frame, group_by=("year",))

    assert result.loc[0, "informal_employment_share"] == pytest.approx(40.0)
    assert result.loc[0, "weighted_denominator"] == pytest.approx(5.0)


def test_monthly_metric_has_one_row_per_observed_month(
    harmonized_metrics_frame: pd.DataFrame,
) -> None:
    result = unemployment_rate(harmonized_metrics_frame)

    assert result[["year", "month"]].values.tolist() == [[2023, 1], [2023, 2]]
    assert result["unemployment_rate"].tolist() == pytest.approx([25.0, 0.0])


def test_missing_metric_column_has_clear_error(
    harmonized_metrics_frame: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="Missing columns"):
        unemployment_rate(harmonized_metrics_frame.drop(columns="vesa"))
