from pathlib import Path

import pandas as pd

from labor_market_analysis.analysis import run_analysis


def test_analysis_creates_tables_and_figures(
    tmp_path: Path, harmonized_metrics_frame: pd.DataFrame
) -> None:
    processed = tmp_path / "processed" / "year=2023"
    processed.mkdir(parents=True)
    harmonized_metrics_frame.drop(columns="year").to_parquet(
        processed / "part-00-00000.parquet", index=False
    )

    outputs = run_analysis(tmp_path / "processed", tmp_path / "reports")

    assert outputs["monthly_unemployment"].is_file()
    assert outputs["unemployment_trend_figure"].is_file()
    monthly = pd.read_csv(outputs["monthly_unemployment"])
    assert monthly["unemployment_rate"].tolist() == [25.0, 0.0]
