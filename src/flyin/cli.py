"""Command-line entry point (REQ-CLI-1).

The CLI accepts the path to a map file, runs the simulate→validate pipeline and prints the official
per-turn lines to stdout. All diagnostics and the optional colored panel go to stderr.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the `fly-in` command."""
    parser = argparse.ArgumentParser(
        prog="fly-in",
        description="42 Fly-in — route drones from start_hub to end_hub.",
    )
    parser.add_argument("map_file", type=Path, help="path to the map .txt file")
    parser.add_argument(
        "--visual",
        action="store_true",
        help="render the colored panel on stderr (REQ-VIS-1)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI; return a process exit code (0 on success)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    map_file: Path = args.map_file
    if not map_file.is_file():
        print(f"error: map file not found: {map_file}", file=sys.stderr)
        return 1

    # TODO(F1+): parse → plan → simulate → validate → print official lines to stdout.
    print(f"fly-in: skeleton ready, pipeline pending for {map_file}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
