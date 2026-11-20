"""Command-line entry point (REQ-CLI-1).

The CLI accepts a map file, builds the F3.6 single-route plan and simulates it, printing the
official per-turn lines to stdout. `--visual` adds a colored panel on stderr without touching
stdout. The independent F7 validator is not wired yet.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from flyin.domain.drone import Drone, make_fleet
from flyin.parsing.errors import MapError
from flyin.parsing.input_rules import load_map
from flyin.parsing.parser import ParsedMap
from flyin.pathfinding.dijkstra import DijkstraPathFinder
from flyin.rendering.renderer import Renderer
from flyin.routing.allocator import assign_single_route
from flyin.simulation.simulator import Simulation


def _build_fleet(parsed: ParsedMap) -> list[Drone]:
    """F3.6: build the fleet with one shared shortest route."""
    path = DijkstraPathFinder().find(parsed.graph, parsed.start, parsed.end)
    return assign_single_route(make_fleet(parsed.nb_drones, parsed.start), path)


def _run_propuesta_a(
    parsed: ParsedMap,
    fleet: list[Drone],
    on_turn: Callable[[int, str], None] | None = None,
) -> list[str]:
    """Simulate the assigned fleet, optionally notifying the visual renderer."""
    return Simulation(parsed.graph, fleet, parsed.end).run(on_turn=on_turn)


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

    try:
        fleet = _build_fleet(parsed)
        renderer = (
            Renderer(parsed.graph, fleet, stream=sys.stderr) if args.visual else None
        )
        on_turn = renderer.render if renderer is not None else None
        lines = _run_propuesta_a(parsed, fleet, on_turn)
    except (ValueError, RuntimeError, KeyError) as exc:
        print(f"error: cannot simulate map: {exc}", file=sys.stderr)
        return 1

    if lines:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
