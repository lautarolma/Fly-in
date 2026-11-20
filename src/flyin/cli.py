"""Command-line entry point (REQ-CLI-1).

The CLI accepts a map file, builds the F3.6 single-route plan and simulates it, printing the
official per-turn lines to stdout. The independent F7 validator and the optional colored panel
are not wired yet; diagnostics already go to stderr.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from flyin.domain.drone import make_fleet
from flyin.parsing.errors import MapError
from flyin.parsing.input_rules import load_map
from flyin.parsing.parser import ParsedMap
from flyin.pathfinding.dijkstra import DijkstraPathFinder
from flyin.routing.allocator import assign_single_route
from flyin.simulation.simulator import Simulation


def _run_propuesta_a(parsed: ParsedMap) -> list[str]:
    """F3.6: one shortest path for the whole fleet, then simulate it."""
    path = DijkstraPathFinder().find(parsed.graph, parsed.start, parsed.end)
    drones = assign_single_route(make_fleet(parsed.nb_drones, parsed.start), path)
    return Simulation(parsed.graph, drones, parsed.end).run()


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
        parsed = load_map(map_file)
    except FileNotFoundError:
        print(f"error: map file not found: {map_file}", file=sys.stderr)
        return 1
    except MapError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: cannot read {map_file}: {exc}", file=sys.stderr)
        return 1

    lines = _run_propuesta_a(parsed)
    if lines:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
