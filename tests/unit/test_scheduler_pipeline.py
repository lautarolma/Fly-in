"""F5 policy hardening: `Scheduler.plan()` over every mandatory map.

The F5 chain was previously tested through its parts (`test_allocator.py`) and
through the CLI mock (`test_cli.py`), but never through the public `plan()`
pipeline itself. These tests close that gap without importing private helpers
from other test modules.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flyin.domain.drone import Drone, DroneState, make_fleet
from flyin.parsing.input_rules import load_map
from flyin.parsing.parser import ParsedMap
from flyin.routing.allocator import Allocator, assign_routes
from flyin.routing.route_builder import RouteBuilder
from flyin.routing.scheduler import Scheduler
from flyin.simulation.simulator import Simulation
from tests.trace import assert_trace_respects_caps

MANDATORY_MAPS = sorted(
    path.relative_to("maps")
    for path in Path("maps").glob("*/*.txt")
    if "challenger" not in path.parts
)


def _manual_plan(parsed: ParsedMap) -> list[Drone]:
    """Compose F5.1 → F5.5 explicitly, mirroring `Scheduler.plan()`."""
    graph = parsed.graph
    candidates = RouteBuilder().build_for_fleet(
        graph, parsed.start, parsed.end, k=4, nb_drones=parsed.nb_drones
    )
    routes = Scheduler().select_routes(graph, candidates, parsed.nb_drones)
    assignment = Allocator().assign(graph, routes, parsed.nb_drones)
    return assign_routes(make_fleet(parsed.nb_drones, parsed.start), assignment)


@pytest.mark.parametrize("map_path", MANDATORY_MAPS)
def test_plan_matches_manual_pipeline(map_path: Path, maps_dir: Path) -> None:
    """`plan()` equals the explicit chain on every mandatory map."""
    parsed = load_map(maps_dir / map_path)

    actual = Scheduler().plan(
        parsed.graph, parsed.start, parsed.end, parsed.nb_drones
    )

    assert actual == _manual_plan(parsed)


@pytest.mark.parametrize("map_path", MANDATORY_MAPS)
def test_plan_is_deterministic_and_fresh(map_path: Path, maps_dir: Path) -> None:
    """Two calls give the same plan, but never reuse a fleet object or state."""
    parsed = load_map(maps_dir / map_path)

    first = Scheduler().plan(
        parsed.graph, parsed.start, parsed.end, parsed.nb_drones
    )
    second = Scheduler().plan(
        parsed.graph, parsed.start, parsed.end, parsed.nb_drones
    )

    assert first == second
    assert all(a is not b for a, b in zip(first, second))
    assert [drone.id for drone in first] == [
        f"D{index}" for index in range(1, parsed.nb_drones + 1)
    ]
    assert all(drone.state is DroneState.WAITING for drone in first)
    assert all(drone.waypoint_index == 0 for drone in first)
    assert all(not drone.is_delivered for drone in first)
    assert all(drone.current_zone == parsed.start for drone in first)


@pytest.mark.parametrize("map_path", MANDATORY_MAPS)
def test_plan_fleet_completes_when_simulated(map_path: Path, maps_dir: Path) -> None:
    """The planned fleet reaches `end` without violating capacities."""
    parsed = load_map(maps_dir / map_path)
    fleet = Scheduler().plan(
        parsed.graph, parsed.start, parsed.end, parsed.nb_drones
    )

    lines = Simulation(parsed.graph, fleet, parsed.end).run()

    assert lines
    final = assert_trace_respects_caps(
        parsed.graph,
        lines,
        start=parsed.start,
        drone_ids=[drone.id for drone in fleet],
    )
    assert set(final.values()) == {parsed.end}
