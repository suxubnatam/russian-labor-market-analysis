from labor_market_analysis.cli import build_parser


def test_cli_exposes_expected_commands() -> None:
    parser = build_parser()

    assert parser.parse_args(["validate"]).command == "validate"
    assert parser.parse_args(["build"]).command == "build"
    assert parser.parse_args(["analyze"]).command == "analyze"
