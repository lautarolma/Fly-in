"""Command-line entry point (REQ-CLI-1).

The CLI accepts the path to a map file, runs the simulate→validate pipeline and prints the official
per-turn lines to stdout. All diagnostics and the optional colored panel go to stderr.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from flyin.parsing.errors import MapError
from flyin.parsing.input_rules import load_map


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
    """Run the CLI; return a process exit code (0 on success, non-zero on any input error)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    map_file: Path = args.map_file
    try:
        load_map(map_file)
    except FileNotFoundError:
        print(f"error: map file not found: {map_file}", file=sys.stderr)
        return 1
    except MapError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: cannot read {map_file}: {exc}", file=sys.stderr)
        return 1

    # TODO(F2+): plan → simulate → validate → print official lines to stdout.
    # Until then, a validated map is a successful run with no turns to emit.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
