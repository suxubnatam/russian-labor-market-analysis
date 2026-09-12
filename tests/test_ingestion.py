from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from labor_market_analysis.ingestion import build_dataset, validate_source_directory


def _write_source(path: Path) -> None:
    frame = pd.DataFrame(
        {
            "GOD": [2022, 2022, 2023],
            "KWARTAL": [1, 1, 1],
            "MES": [1, 2, 1],
            "TERRIT": [45, 45, 3],
            "VESA": [2.0, 1.0, 1.0],
            "VESA_KVART": [2.0, 1.0, 1.0],
            "VESA_OB": [2.0, 1.0, 1.0],
            "POSSEL": [1, 1, 2],
            "NAS_POL": [1, 2, 2],
            "NAS_VOZR": [30, 31, 22],
            "STRUKTAK": [1, 2, 1],
            "ZAN_NF": [0, 1, 1],
        }
    )
    pyreadstat.write_sav(frame, str(path))


def test_validates_and_builds_partitioned_dataset(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    output = tmp_path / "processed"
    raw.mkdir()
    _write_source(raw / "survey.sav")

    info = validate_source_directory(raw)
    summary = build_dataset(raw, output, chunk_size=2)

    assert len(info) == 1
    assert summary.source_files == 1
    assert summary.rows == 3
    assert summary.years == (2022, 2023)
    assert list(output.glob("year=2022/*.parquet"))
    assert list(output.glob("year=2023/*.parquet"))


def test_refuses_to_overwrite_existing_dataset(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    output = tmp_path / "processed"
    raw.mkdir()
    _write_source(raw / "survey.sav")
    build_dataset(raw, output)

    with pytest.raises(FileExistsError, match="already contains"):
        build_dataset(raw, output)
