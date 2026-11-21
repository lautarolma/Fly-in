"""Estimator tests: admissible makespan bounds and their capacity collar (F5.3)."""

from __future__ import annotations

from pathlib import Path as FilePath

import pytest

from flyin.domain.connection import Connection
from flyin.domain.drone import make_fleet
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone
from flyin.parsing.parser import parse_map
from flyin.pathfinding.base import Path
from flyin.pathfinding.dijkstra import DijkstraPathFinder
from flyin.routing.allocator import assign_single_route
from flyin.routing.estimator import (
    UNBOUNDED,
    MakespanEstimator,
    bottleneck_capacity,
    route_bound,
)
from flyin.routing.route_builder import RouteBuilder
from flyin.simulation.simulator import Simulation

MAP_FILES = sorted(
    path
    for path in FilePath("maps").glob("*/*.txt")
    if "challenger" not in path.parts
)


def test_estimate_with_capacity_one_is_the_lem_in_bound() -> None:
    assert MakespanEstimator().estimate([3], [4], [1]) == 6


def test_estimate_shrinks_injection_time_with_capacity() -> None:
    assert MakespanEstimator().estimate([3], [4], [2]) == 4


def test_estimate_is_the_max_across_routes() -> None:
    assert MakespanEstimator().estimate([3, 5], [4, 2], [2, 1]) == 6


def test_unused_route_contributes_nothing() -> None:
    assert MakespanEstimator().estimate([1, 5], [3, 0], [1, 1]) == 3


def test_empty_estimation_is_zero() -> None:
    assert MakespanEstimator().estimate([], [], []) == 0


def test_unbounded_capacity_behaves_as_infinite() -> None:
    assert MakespanEstimator().estimate([3], [4], [UNBOUNDED]) == 3


@pytest.mark.parametrize(
    ("costs", "loads", "caps"),
    [
        ([3], [4], []),
        ([3], [], [1]),
        ([3], [-1], [1]),
        ([-1], [4], [1]),
        ([3], [4], [0]),
    ],
)
def test_estimate_rejects_invalid_inputs(
    costs: list[int], loads: list[int], caps: list[int]
) -> None:
    with pytest.raises(ValueError):
        MakespanEstimator().estimate(costs, loads, caps)


# --- fleet_bound: cota a nivel flota sobre el subconjunto elegido -------


def test_fleet_bound_returns_zero_when_there_is_nothing_to_assign() -> None:
    estimator = MakespanEstimator()
    assert estimator.fleet_bound(Graph(), [], 3) == 0
    assert estimator.fleet_bound(Graph(), [], 0) == 0


def test_fleet_bound_is_the_structural_bound_on_a_single_route() -> None:
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0, cap=None))
    graph.add_zone(Zone(name="mid", x=1, y=0, cap=2))
    graph.add_zone(Zone(name="goal", x=2, y=0, cap=None))
    graph.add_connection(Connection(a="start", b="mid", cap=1))
    graph.add_connection(Connection(a="mid", b="goal", cap=5))
    route = Path(zones=("start", "mid", "goal"), cost=2)

    assert MakespanEstimator().fleet_bound(graph, [route], 4) == 5


def test_fleet_bound_on_easy02_is_four_turns() -> None:
    parsed = parse_map(FilePath("maps/easy/02_simple_fork.txt"))
    routes = RouteBuilder().build_for_fleet(
        parsed.graph, parsed.start, parsed.end, k=4, nb_drones=parsed.nb_drones
    )

    assert MakespanEstimator().fleet_bound(parsed.graph, routes, parsed.nb_drones) == 4


# --- route_bound: la fórmula de la cota, dueña única --------------------


def test_route_bound_is_the_lem_in_bound_at_capacity_one() -> None:
    assert route_bound(3, 4, 1) == 6


def test_route_bound_shrinks_the_injection_term_with_capacity() -> None:
    assert route_bound(3, 4, 2) == 4


def test_route_bound_is_zero_for_an_unused_route() -> None:
    """Una ruta sin drones no aporta al máximo (no el `cost - 1` sin sentido)."""
    assert route_bound(3, 0, 1) == 0


@pytest.mark.parametrize(
    ("cost", "load", "cap"),
    [(-1, 4, 1), (3, -1, 1), (3, 4, 0)],
)
def test_route_bound_rejects_invalid_inputs(cost: int, load: int, cap: int) -> None:
    with pytest.raises(ValueError):
        route_bound(cost, load, cap)


def test_bottleneck_is_the_tightest_zone_or_link() -> None:
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0, cap=None))
    graph.add_zone(Zone(name="mid", x=1, y=0, cap=2))
    graph.add_zone(Zone(name="goal", x=2, y=0, cap=None))
    graph.add_connection(Connection(a="start", b="mid", cap=1))
    graph.add_connection(Connection(a="mid", b="goal", cap=5))
    route = Path(zones=("start", "mid", "goal"), cost=2)

    assert bottleneck_capacity(graph, route) == 1


def test_bottleneck_ignores_uncapped_hubs() -> None:
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0, cap=None))
    graph.add_zone(Zone(name="mid", x=1, y=0, cap=None))
    graph.add_zone(Zone(name="goal", x=2, y=0, cap=None))
    graph.add_connection(Connection(a="start", b="mid", cap=3))
    graph.add_connection(Connection(a="mid", b="goal", cap=4))
    route = Path(zones=("start", "mid", "goal"), cost=2)

    assert bottleneck_capacity(graph, route) == 3


@pytest.mark.parametrize("map_file", MAP_FILES, ids=lambda path: str(path))
def test_estimate_is_a_lower_bound_on_mandatory_maps(map_file: FilePath) -> None:
    parsed = parse_map(map_file)
    route = DijkstraPathFinder().find(parsed.graph, parsed.start, parsed.end)
    cap = bottleneck_capacity(parsed.graph, route)
    estimate = MakespanEstimator().estimate(
        [route.cost], [parsed.nb_drones], [cap]
    )

    fleet = assign_single_route(
        make_fleet(parsed.nb_drones, parsed.start), route
    )
    actual = len(Simulation(parsed.graph, fleet, parsed.end).run())

    assert actual > 0
    assert estimate <= actual, f"{map_file}: {estimate} > {actual}"
