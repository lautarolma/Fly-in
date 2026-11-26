"""Command-line entry point (REQ-CLI-1).

The CLI accepts a map file, asks the `Scheduler` for the best validated fleet
(routing policy: k candidates -> best valid subset -> ETA assignment, F6.4) and
prints that schedule's official per-turn lines to stdout. `--visual` re-simulates
only the winning fleet with a colored panel on stderr, so failed retries never
render. The independent F7 validator gates stdout before any line is printed.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from flyin.domain.drone import Drone
from flyin.parsing.errors import MapError
from flyin.parsing.input_rules import load_map
from flyin.parsing.parser import ParsedMap
from flyin.rendering.renderer import Renderer
from flyin.routing.scheduler import Scheduler
from flyin.simulation.simulator import Simulation
from flyin.validation import ScheduleError, Validator


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
        validated = Scheduler().plan_validated(
            parsed.graph, parsed.start, parsed.end, parsed.nb_drones
        )
        renderer = (
            Renderer(parsed.graph, validated.fleet, stream=sys.stderr)
            if args.visual
            else None
        )
        on_turn = renderer.render if renderer is not None else None
        if on_turn is not None:
            # Re-simulate only the winner to paint; stdout uses the validated lines.
            _run_propuesta_a(parsed, validated.fleet, on_turn)
        lines = validated.lines
        Validator(parsed).validate(lines)
    except ScheduleError as exc:
        print(f"error: invalid schedule: {exc}", file=sys.stderr)
        return 1
    except (ValueError, RuntimeError, KeyError) as exc:
        print(f"error: cannot simulate map: {exc}", file=sys.stderr)
        return 1

    if lines:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
