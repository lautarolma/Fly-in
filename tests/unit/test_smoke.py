"""Smoke tests: the package imports and the CLI is wired (F0)."""

from __future__ import annotations

from flyin import __version__
from flyin.cli import build_parser


def test_package_exposes_version() -> None:
    assert __version__ == "0.1.0"


def test_cli_parses_map_argument() -> None:
    args = build_parser().parse_args(["maps/easy/01_linear_path.txt"])
    assert str(args.map_file) == "maps/easy/01_linear_path.txt"
    assert args.visual is False
