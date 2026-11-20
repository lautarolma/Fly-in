"""F5.4: the chosen route subset must minimize the estimated makespan."""

from __future__ import annotations

from pathlib import Path as FilePath

import pytest

from flyin.domain.connection import Connection
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone
from flyin.parsing.parser import parse_map
from flyin.pathfinding.base import Path
from flyin.routing.estimator import MakespanEstimator, bottleneck_capacity
from flyin.routing.route_builder import RouteBuilder


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


def _bound(graph: Graph, routes: list[Path], nb_drones: int) -> int:
    """Independently derive the bound of a balanced split."""
    base, extra = divmod(nb_drones, len(routes))
    loads = [base + (1 if i < extra else 0) for i in range(len(routes))]
    return MakespanEstimator().estimate(
        [route.cost for route in routes],
        loads,
        [bottleneck_capacity(graph, route) for route in routes],
    )


def test_select_returns_empty_without_candidates() -> None:
    assert MakespanEstimator().select_routes(_graph(), [], 4) == []


def test_select_returns_empty_without_drones() -> None:
    graph = _graph()
    routes = [_route(graph, "a", cost=3, cap=1)]

    assert MakespanEstimator().select_routes(graph, routes, 0) == []


def test_select_rejects_negative_fleet() -> None:
    with pytest.raises(ValueError):
        MakespanEstimator().select_routes(_graph(), [], -1)


def test_select_rejects_an_unbounded_candidate_set() -> None:
    graph = _graph()
    routes = [_route(graph, str(index), cost=2, cap=1) for index in range(5)]

    with pytest.raises(ValueError):
        MakespanEstimator().select_routes(graph, routes, 4)


def test_select_with_a_single_candidate() -> None:
    graph = _graph()
    route = _route(graph, "a", cost=3, cap=1)

    assert MakespanEstimator().select_routes(graph, [route], 2) == [route]


def test_select_adds_a_route_when_the_bound_drops() -> None:
    graph = _graph()
    first = _route(graph, "a", cost=3, cap=1)
    second = _route(graph, "b", cost=3, cap=1)

    assert _bound(graph, [first], 4) == 6
    assert _bound(graph, [first, second], 4) == 4
    assert MakespanEstimator().select_routes(graph, [first, second], 4) == [
        first,
        second,
    ]


def test_select_prefers_fewer_routes_on_a_tie() -> None:
    graph = _graph()
    first = _route(graph, "a", cost=3, cap=1)
    second = _route(graph, "b", cost=3, cap=1)

    assert _bound(graph, [first], 1) == _bound(graph, [first, second], 1)
    assert MakespanEstimator().select_routes(graph, [first, second], 1) == [first]


def test_select_discards_a_route_that_raises_the_bound() -> None:
    graph = _graph()
    fast = _route(graph, "a", cost=3, cap=1)
    slow = _route(graph, "b", cost=10, cap=1)

    assert MakespanEstimator().select_routes(graph, [fast, slow], 2) == [fast]


def test_select_accounts_for_capacity_not_only_cost() -> None:
    graph = _graph()
    narrow = _route(graph, "narrow", cost=3, cap=1)
    wide = _route(graph, "wide", cost=3, cap=4)

    assert MakespanEstimator().select_routes(graph, [narrow, wide], 8) == [wide]


def test_select_never_uses_more_routes_than_drones() -> None:
    graph = _graph()
    routes = [_route(graph, label, cost=2, cap=1) for label in "abcd"]

    chosen = MakespanEstimator().select_routes(graph, routes, 2)

    assert 0 < len(chosen) <= 2


def test_select_is_deterministic_and_preserves_candidate_order() -> None:
    graph = _graph()
    routes = [
        _route(graph, "a", cost=4, cap=1),
        _route(graph, "b", cost=3, cap=2),
        _route(graph, "c", cost=3, cap=1),
    ]
    estimator = MakespanEstimator()

    first = estimator.select_routes(graph, routes, 5)
    assert first == estimator.select_routes(graph, routes, 5)
    assert first == [route for route in routes if route in first]


def test_selection_never_worsens_the_bound_on_a_real_map() -> None:
    parsed = parse_map(FilePath("maps/easy/02_simple_fork.txt"))
    candidates = RouteBuilder().build_for_fleet(
        parsed.graph, parsed.start, parsed.end, k=4, nb_drones=parsed.nb_drones
    )
    assert candidates

    chosen = MakespanEstimator().select_routes(
        parsed.graph, candidates, parsed.nb_drones
    )

    assert chosen
    assert all(route in candidates for route in chosen)
    assert len(chosen) <= parsed.nb_drones
    assert _bound(parsed.graph, chosen, parsed.nb_drones) <= _bound(
        parsed.graph, [candidates[0]], parsed.nb_drones
    )
