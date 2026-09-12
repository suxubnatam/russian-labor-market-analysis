"""Command-line interface for validation, dataset building, and analysis."""

import argparse
import json
from pathlib import Path

from labor_market_analysis.config import (
    DEFAULT_PROCESSED_DIR,
    DEFAULT_RAW_DIR,
    DEFAULT_REPORT_DIR,
)
from labor_market_analysis.ingestion import build_dataset, validate_source_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="labor-market",
        description="Пайплайн анализа российского рынка труда за 2010–2023 годы.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate", help="Проверить наличие и схему исходных SPSS-файлов."
    )
    validate_parser.add_argument("--input", type=Path, default=DEFAULT_RAW_DIR)

    build_parser_command = subparsers.add_parser(
        "build", help="Собрать гармонизированный Parquet-набор."
    )
    build_parser_command.add_argument("--input", type=Path, default=DEFAULT_RAW_DIR)
    build_parser_command.add_argument("--output", type=Path, default=DEFAULT_PROCESSED_DIR)
    build_parser_command.add_argument("--chunk-size", type=int, default=100_000)
    build_parser_command.add_argument("--overwrite", action="store_true")

    analysis_parser = subparsers.add_parser(
        "analyze", help="Построить итоговые таблицы и визуализации."
    )
    analysis_parser.add_argument("--input", type=Path, default=DEFAULT_PROCESSED_DIR)
    analysis_parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_DIR)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        if args.command == "validate":
            files = validate_source_directory(args.input)
            result = {
                "status": "ok",
                "source_files": len(files),
                "files": [Path(info.path).name for info in files],
            }
        elif args.command == "build":
            result = build_dataset(
                args.input,
                args.output,
                chunk_size=args.chunk_size,
                overwrite=args.overwrite,
            ).as_dict()
        else:
            from labor_market_analysis.analysis import run_analysis

            outputs = run_analysis(args.input, args.output)
            result = {name: str(path) for name, path in outputs.items()}
    except (FileNotFoundError, FileExistsError, ValueError) as error:
        raise SystemExit(f"error: {error}") from error
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
