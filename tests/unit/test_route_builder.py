"""RouteBuilder tests: diverse k-routes with real costs (F5.1)."""

from __future__ import annotations

import pytest

from flyin.domain.connection import Connection
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone, ZoneType
from flyin.pathfinding.base import Path
from flyin.routing.route_builder import MAX_ROUTES, RouteBuilder, cap_route_count


def _linear_graph() -> Graph:
    """`start -hub-> goal`, all zones NORMAL (enter_cost 1)."""
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0))
    graph.add_zone(Zone(name="hub", x=1, y=0))
    graph.add_zone(Zone(name="goal", x=2, y=0))
    graph.add_connection(Connection(a="start", b="hub"))
    graph.add_connection(Connection(a="hub", b="goal"))
    return graph


def _two_corridors() -> Graph:
    """Two equal-cost corridors: via `slow` or via `a`->`b`."""
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0))
    graph.add_zone(Zone(name="slow", x=1, y=0, type=ZoneType.RESTRICTED))
    graph.add_zone(Zone(name="a", x=0, y=1))
    graph.add_zone(Zone(name="b", x=1, y=1))
    graph.add_zone(Zone(name="goal", x=2, y=0))
    graph.add_connection(Connection(a="start", b="slow"))
    graph.add_connection(Connection(a="slow", b="goal"))
    graph.add_connection(Connection(a="start", b="a"))
    graph.add_connection(Connection(a="a", b="b"))
    graph.add_connection(Connection(a="b", b="goal"))
    return graph


def _fan_graph(corridors: int) -> Graph:
    """`start` to `goal` through `corridors` independent middle zones."""
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0))
    graph.add_zone(Zone(name="goal", x=10, y=0))
    for index in range(corridors):
        middle = f"mid{index}"
        graph.add_zone(Zone(name=middle, x=index, y=1))
        graph.add_connection(Connection(a="start", b=middle))
        graph.add_connection(Connection(a=middle, b="goal"))
    return graph


def test_build_returns_shortest_route_first() -> None:
    routes = RouteBuilder().build(_linear_graph(), "start", "goal", 1)
    assert routes == [Path(zones=("start", "hub", "goal"), cost=2)]


def test_build_returns_distinct_routes() -> None:
    routes = RouteBuilder().build(_two_corridors(), "start", "goal", 2)
    assert len(routes) == 2
    assert {route.zones for route in routes} == {
        ("start", "a", "b", "goal"),
        ("start", "slow", "goal"),
    }


def test_build_reports_real_costs_not_penalized() -> None:
    routes = RouteBuilder().build(_two_corridors(), "start", "goal", 2)
    assert [route.cost for route in routes] == [3, 3]


def test_build_switches_to_longer_corridor_after_penalty() -> None:
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0))
    graph.add_zone(Zone(name="short", x=1, y=0))
    graph.add_zone(Zone(name="x", x=0, y=1))
    graph.add_zone(Zone(name="y", x=1, y=1))
    graph.add_zone(Zone(name="goal", x=2, y=0))
    graph.add_connection(Connection(a="start", b="short"))
    graph.add_connection(Connection(a="short", b="goal"))
    graph.add_connection(Connection(a="start", b="x"))
    graph.add_connection(Connection(a="x", b="y"))
    graph.add_connection(Connection(a="y", b="goal"))

    routes = RouteBuilder(penalty=2).build(graph, "start", "goal", 2)

    assert [route.zones for route in routes] == [
        ("start", "short", "goal"),
        ("start", "x", "y", "goal"),
    ]
    assert [route.cost for route in routes] == [2, 3]


def test_build_stops_when_only_one_route_exists() -> None:
    routes = RouteBuilder().build(_linear_graph(), "start", "goal", 5)
    assert len(routes) == 1
    assert routes[0].zones == ("start", "hub", "goal")


@pytest.mark.parametrize("k", [0, -1])
def test_build_nonpositive_k_returns_empty(k: int) -> None:
    assert RouteBuilder().build(_linear_graph(), "start", "goal", k) == []


def test_build_start_equals_goal() -> None:
    routes = RouteBuilder().build(_linear_graph(), "start", "start", 3)
    assert routes == [Path(zones=("start",), cost=0)]


def test_build_does_not_mutate_graph_or_previous_routes() -> None:
    graph = _two_corridors()
    before = dict(graph.zones)
    builder = RouteBuilder()

    first = builder.build(graph, "start", "goal", 2)
    second = builder.build(graph, "start", "goal", 2)

    assert graph.zones == before
    assert first == second


def test_build_rejects_nonpositive_penalty() -> None:
    with pytest.raises(ValueError):
        RouteBuilder(penalty=0)


@pytest.mark.parametrize(
    ("k", "nb_drones", "expected"),
    [(8, 10, 4), (8, 2, 2), (3, 10, 3), (0, 10, 0), (-1, 10, 0), (3, 0, 0)],
)
def test_cap_route_count(k: int, nb_drones: int, expected: int) -> None:
    assert cap_route_count(k, nb_drones) == expected
    assert expected <= MAX_ROUTES


def test_build_never_exceeds_max_routes() -> None:
    routes = RouteBuilder().build(_fan_graph(6), "start", "goal", 100)
    assert len(routes) == MAX_ROUTES
    assert len({route.zones for route in routes}) == MAX_ROUTES


def test_build_for_fleet_caps_by_drone_count() -> None:
    routes = RouteBuilder().build_for_fleet(
        _fan_graph(6), "start", "goal", 8, 2
    )
    assert len(routes) == 2


def test_build_for_fleet_caps_by_max_routes() -> None:
    routes = RouteBuilder().build_for_fleet(
        _fan_graph(6), "start", "goal", 100, 25
    )
    assert len(routes) == MAX_ROUTES
