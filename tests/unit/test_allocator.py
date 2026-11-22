"""Assignment: F3.6 single-route fleet (Propuesta A) and F5.5 ETA-greedy reparto."""

from __future__ import annotations

from pathlib import Path as FilePath
from typing import NamedTuple

import pytest

from flyin.domain.connection import Connection
from flyin.domain.drone import Drone, DroneState, make_fleet
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone
from flyin.parsing.parser import ParsedMap, parse_map
from flyin.pathfinding.base import Path
from flyin.pathfinding.dijkstra import DijkstraPathFinder
from flyin.routing.allocator import Allocator, assign_routes, assign_single_route
from flyin.routing.estimator import MakespanEstimator, bottleneck_capacity
from flyin.routing.route_builder import RouteBuilder
from flyin.routing.scheduler import Scheduler
from flyin.simulation.simulator import Simulation

MANDATORY_MAPS = sorted(
    path
    for path in FilePath("maps").glob("*/*.txt")
    if "challenger" not in path.parts
)

ROUTE = Path(zones=("start", "mid", "goal"), cost=2)


# --- F3.6: single route ------------------------------------------------


def test_assign_single_route_resets_cursor_and_transit_state() -> None:
    """Un dron reutilizado vuelve a WAITING con el cursor en cero."""
    drones = [
        Drone(
            id="D1",
            route=("start",),
            waypoint_index=3,
            state=DroneState.DELIVERED,
            target="old",
            transit_turns_left=2,
        )
    ]
    assigned = assign_single_route(drones, ROUTE)
    assert len(assigned) == 1
    assert assigned[0].id == "D1"
    assert assigned[0].route == ROUTE.zones
    assert assigned[0].waypoint_index == 0
    assert assigned[0].state is DroneState.WAITING
    assert assigned[0].target is None
    assert assigned[0].transit_turns_left == 0
    assert assigned[0].current_zone == "start"
    assert assigned[0].next_zone == "mid"


def test_assign_single_route_does_not_mutate_input() -> None:
    """La asignación es pura: ni la lista ni los drones originales cambian."""
    drones = make_fleet(2, "start")
    assigned = assign_single_route(drones, ROUTE)
    assert [drone.id for drone in assigned] == ["D1", "D2"]
    assert all(drone.route == ROUTE.zones for drone in assigned)
    assert all(assigned[index] is not drones[index] for index in range(2))
    assert [drone.route for drone in drones] == [("start",), ("start",)]


def test_assign_single_route_empty_fleet() -> None:
    """Una flota vacía devuelve una lista vacía, sin efectos."""
    assert assign_single_route([], ROUTE) == []


# --- F5.5: helpers -----------------------------------------------------


def _graph() -> Graph:
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0, cap=None))
    graph.add_zone(Zone(name="goal", x=9, y=0, cap=None))
    return graph


def _route(graph: Graph, label: str, cost: int, cap: int) -> Path:
    middle = f"{label}_mid"
    graph.add_zone(Zone(name=middle, x=len(graph.zones), y=0, cap=cap))
    graph.add_connection(Connection(a="start", b=middle, cap=cap))
    graph.add_connection(Connection(a=middle, b="goal", cap=cap))
    return Path(zones=("start", middle, "goal"), cost=cost)


def _loads(assignment: list[Path], routes: list[Path]) -> list[int]:
    """Count how many drones landed on each candidate route."""
    return [assignment.count(route) for route in routes]


# --- F5.5: the greedy --------------------------------------------------


def test_assign_returns_one_route_per_drone() -> None:
    graph = _graph()
    routes = [_route(graph, "a", cost=3, cap=1), _route(graph, "b", cost=5, cap=1)]

    assignment = Allocator().assign(graph, routes, 5)

    assert len(assignment) == 5
    assert all(route in routes for route in assignment)


def test_assign_is_deterministic() -> None:
    graph = _graph()
    routes = [
        _route(graph, "a", cost=3, cap=2),
        _route(graph, "b", cost=4, cap=1),
    ]
    allocator = Allocator()

    first = allocator.assign(graph, routes, 7)

    assert first == allocator.assign(graph, routes, 7)


def test_assign_spreads_equal_routes_evenly() -> None:
    """Dos corredores idénticos reparten la flota e intercalan los ids."""
    graph = _graph()
    routes = [
        _route(graph, "a", cost=3, cap=1),
        _route(graph, "b", cost=3, cap=1),
    ]

    assignment = Allocator().assign(graph, routes, 4)

    assert _loads(assignment, routes) == [2, 2]
    assert assignment == [routes[0], routes[1], routes[0], routes[1]]


def test_assign_keeps_drones_on_the_cheap_route_while_it_wins() -> None:
    """El greedy no balancea por balancear: respeta el costo de la cota."""
    graph = _graph()
    routes = [
        _route(graph, "fast", cost=3, cap=1),
        _route(graph, "slow", cost=10, cap=1),
    ]

    assignment = Allocator().assign(graph, routes, 4)

    assert _loads(assignment, routes) == [4, 0]


def test_assign_fills_the_wide_route_before_the_narrow_one() -> None:
    """Mismo costo: el cuello de botella más ancho absorbe más drones."""
    graph = _graph()
    routes = [
        _route(graph, "narrow", cost=3, cap=1),
        _route(graph, "wide", cost=3, cap=4),
    ]

    assignment = Allocator().assign(graph, routes, 4)

    assert _loads(assignment, routes) == [1, 3]


def test_assign_empty_fleet_returns_no_route() -> None:
    graph = _graph()
    routes = [_route(graph, "a", cost=3, cap=1)]

    assert Allocator().assign(graph, routes, 0) == []


def test_assign_rejects_a_fleet_without_routes() -> None:
    with pytest.raises(ValueError):
        Allocator().assign(_graph(), [], 3)


def test_assign_rejects_a_negative_fleet() -> None:
    graph = _graph()
    routes = [_route(graph, "a", cost=3, cap=1)]

    with pytest.raises(ValueError):
        Allocator().assign(graph, routes, -1)


# --- F5.5: applying the plan to the fleet ------------------------------


def test_assign_routes_applies_one_route_per_drone() -> None:
    graph = _graph()
    routes = [_route(graph, "a", cost=3, cap=1), _route(graph, "b", cost=5, cap=1)]
    assignment = Allocator().assign(graph, routes, 3)

    fleet = assign_routes(make_fleet(3, "start"), assignment)

    assert [drone.route for drone in fleet] == [
        route.zones for route in assignment
    ]
    assert all(drone.waypoint_index == 0 for drone in fleet)
    assert all(drone.state is DroneState.WAITING for drone in fleet)
    assert all(drone.transit_turns_left == 0 for drone in fleet)


def test_assign_routes_rejects_a_mismatched_vector() -> None:
    """Tres drones y una sola ruta: falla en vez de dejar drones sin plan."""
    graph = _graph()
    routes = [_route(graph, "a", cost=3, cap=1)]

    with pytest.raises(ValueError):
        assign_routes(make_fleet(3, "start"), routes)


def test_assign_routes_does_not_mutate_input() -> None:
    graph = _graph()
    routes = [_route(graph, "a", cost=3, cap=1)]
    assignment = Allocator().assign(graph, routes, 2)
    drones = make_fleet(2, "start")

    fleet = assign_routes(drones, assignment)

    assert all(fleet[index] is not drones[index] for index in range(2))
    assert [drone.route for drone in drones] == [("start",), ("start",)]


# --- DoD F5: the reparto has to earn its keep on real maps -------------


class _Reparto(NamedTuple):
    """What the F5.1 → F5.5 pipeline decided, plus what it achieved."""

    routes: list[Path]
    assignment: list[Path]
    bound: int
    makespan: int


def _single_makespan(parsed: ParsedMap) -> int:
    """Makespan of the F3.6 plan the CLI still uses today."""
    route = DijkstraPathFinder().find(parsed.graph, parsed.start, parsed.end)
    fleet = assign_single_route(make_fleet(parsed.nb_drones, parsed.start), route)
    return len(Simulation(parsed.graph, fleet, parsed.end).run())


def _reparto(parsed: ParsedMap) -> _Reparto:
    """Run F5.1 → F5.5 and measure the result on the real simulator."""
    graph, nb = parsed.graph, parsed.nb_drones
    candidates = RouteBuilder().build_for_fleet(
        graph, parsed.start, parsed.end, k=4, nb_drones=nb
    )
    routes = Scheduler().select_routes(graph, candidates, nb)
    assignment = Allocator().assign(graph, routes, nb)
    fleet = assign_routes(make_fleet(nb, parsed.start), assignment)
    return _Reparto(
        routes=routes,
        assignment=assignment,
        bound=MakespanEstimator().estimate(
            [route.cost for route in routes],
            [assignment.count(route) for route in routes],
            [bottleneck_capacity(graph, route) for route in routes],
        ),
        makespan=len(Simulation(graph, fleet, parsed.end).run()),
    )


def _balanced_bound(parsed: ParsedMap, reparto: _Reparto) -> int:
    """The bound `select_routes` scored the subset with (F5.4 assumption)."""
    base, extra = divmod(parsed.nb_drones, len(reparto.routes))
    loads = [
        base + (1 if index < extra else 0) for index in range(len(reparto.routes))
    ]
    return MakespanEstimator().estimate(
        [route.cost for route in reparto.routes],
        loads,
        [bottleneck_capacity(parsed.graph, route) for route in reparto.routes],
    )


@pytest.mark.parametrize("map_file", MANDATORY_MAPS, ids=lambda path: str(path))
def test_greedy_reparto_never_worsens_the_makespan(map_file: FilePath) -> None:
    """DoD F5 (forma débil): multi-ruta nunca pierde contra una sola ruta."""
    parsed = parse_map(map_file)
    single = _single_makespan(parsed)

    assert _reparto(parsed).makespan <= single, f"{map_file} worse than single"


@pytest.mark.parametrize("map_file", MANDATORY_MAPS, ids=lambda path: str(path))
def test_greedy_bound_stays_admissible_on_the_makespan(map_file: FilePath) -> None:
    """La cota de F5.3 sigue valiendo con el reparto de F5.5 encima."""
    reparto = _reparto(parse_map(map_file))

    assert reparto.makespan > 0
    assert reparto.bound <= reparto.makespan, (
        f"{map_file}: bound {reparto.bound} > makespan {reparto.makespan}"
    )


@pytest.mark.parametrize("map_file", MANDATORY_MAPS, ids=lambda path: str(path))
def test_greedy_bound_beats_the_balanced_split_select_routes_assumed(
    map_file: FilePath,
) -> None:
    """F5.4 ↔ F5.5: el reparto real nunca empeora la cota que lo seleccionó."""
    parsed = parse_map(map_file)
    reparto = _reparto(parsed)
    balanced = _balanced_bound(parsed, reparto)

    assert reparto.bound <= balanced, (
        f"{map_file}: greedy {reparto.bound} > balanced {balanced}"
    )


@pytest.mark.parametrize(
    ("category", "map_name"),
    [
        ("easy", "02_simple_fork.txt"),
        ("medium", "03_priority_puzzle.txt"),
    ],
)
def test_greedy_reparto_lowers_the_makespan_when_routes_fork(
    category: str, map_name: str, maps_dir: FilePath
) -> None:
    """DoD F5 (forma estricta): un segundo corredor real debe ganarle a una ruta."""
    parsed = parse_map(maps_dir / category / map_name)
    single = _single_makespan(parsed)

    assert _reparto(parsed).makespan < single, f"{category}/{map_name} did not improve"
