"""Read large SPSS survey files and build a partitioned Parquet dataset."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pyreadstat

from labor_market_analysis.config import COLUMN_ALIASES, CRITICAL_COLUMNS
from labor_market_analysis.harmonization import harmonize_dataframe, normalized_name


@dataclass(frozen=True)
class SourceFileInfo:
    path: str
    columns: tuple[str, ...]
    required_columns: tuple[str, ...]


@dataclass(frozen=True)
class BuildSummary:
    source_files: int
    parquet_parts: int
    rows: int
    years: tuple[int, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def discover_sav_files(raw_dir: Path) -> list[Path]:
    """Find SPSS inputs deterministically."""

    files = sorted(raw_dir.glob("*.sav"))
    if not files:
        raise FileNotFoundError(f"No .sav files found in {raw_dir}")
    return files


def inspect_sav_file(path: Path) -> SourceFileInfo:
    """Read SPSS metadata without loading observations."""

    _, metadata = pyreadstat.read_sav(str(path), metadataonly=True)
    columns = tuple(metadata.column_names)
    canonical = {normalized_name(column) for column in columns}
    available_required = tuple(sorted(CRITICAL_COLUMNS.intersection(canonical)))
    missing = CRITICAL_COLUMNS.difference(canonical)
    if missing:
        raise ValueError(f"{path.name} is missing required fields: {sorted(missing)}")
    return SourceFileInfo(str(path), columns, available_required)


def validate_source_directory(raw_dir: Path) -> list[SourceFileInfo]:
    """Validate all source schemas without reading their row data."""

    return [inspect_sav_file(path) for path in discover_sav_files(raw_dir)]


def iter_sav_chunks(path: Path, chunk_size: int = 100_000):
    """Yield only relevant columns from one SPSS file."""

    info = inspect_sav_file(path)
    use_columns = [
        column
        for column in info.columns
        if str(column).strip().lower() in COLUMN_ALIASES
    ]
    yield from pyreadstat.read_file_in_chunks(
        pyreadstat.read_sav,
        str(path),
        chunksize=chunk_size,
        usecols=use_columns,
        apply_value_formats=False,
    )


def _prepare_output(output_dir: Path, overwrite: bool) -> None:
    existing = list(output_dir.rglob("*.parquet")) if output_dir.exists() else []
    if existing and not overwrite:
        raise FileExistsError(
            f"{output_dir} already contains Parquet files; pass overwrite=True to replace them"
        )
    if overwrite:
        for path in existing:
            path.unlink()
    output_dir.mkdir(parents=True, exist_ok=True)


def build_dataset(
    raw_dir: Path,
    output_dir: Path,
    *,
    chunk_size: int = 100_000,
    overwrite: bool = False,
) -> BuildSummary:
    """Build a memory-bounded, year-partitioned analytical dataset."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    files = discover_sav_files(raw_dir)
    _prepare_output(output_dir, overwrite)

    row_count = 0
    part_count = 0
    observed_years: set[int] = set()
    for file_index, path in enumerate(files):
        for chunk_index, (chunk, _) in enumerate(iter_sav_chunks(path, chunk_size)):
            harmonized = harmonize_dataframe(chunk)
            row_count += len(harmonized)
            for year, partition in harmonized.dropna(subset=["year"]).groupby("year"):
                year_number = int(year)
                observed_years.add(year_number)
                partition_dir = output_dir / f"year={year_number}"
                partition_dir.mkdir(parents=True, exist_ok=True)
                output_path = partition_dir / f"part-{file_index:02d}-{chunk_index:05d}.parquet"
                partition.drop(columns="year").to_parquet(output_path, index=False)
                part_count += 1

    if row_count == 0:
        raise ValueError("No valid observations remained after harmonization")
    return BuildSummary(len(files), part_count, row_count, tuple(sorted(observed_years)))
