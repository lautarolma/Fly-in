"""Pathfinding tests: Dijkstra and A* (F2.2 / F2.3 / F2.4)."""

from __future__ import annotations

from pathlib import Path as FilePath

import pytest

from flyin.domain.connection import Connection
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone, ZoneType
from flyin.parsing.parser import parse_map
from flyin.pathfinding.astar import AStarPathFinder
from flyin.pathfinding.base import PathFinder
from flyin.pathfinding.dijkstra import DijkstraPathFinder

LINKS_EASY_01 = FilePath("maps/easy/01_linear_path.txt")


def _linear_graph() -> Graph:
    """`start -hub-> goal`, all zones NORMAL (enter_cost 1)."""
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0))
    graph.add_zone(Zone(name="hub", x=1, y=0))
    graph.add_zone(Zone(name="goal", x=2, y=0))
    graph.add_connection(Connection(a="start", b="hub"))
    graph.add_connection(Connection(a="hub", b="goal"))
    return graph


def test_dijkstra_returns_minimum_cost_path() -> None:
    finder = DijkstraPathFinder()
    path = finder.find(_linear_graph(), "start", "goal")
    assert path.zones == ("start", "hub", "goal")
    assert path.cost == 2


def test_dijkstra_picks_cheaper_path() -> None:
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0))
    graph.add_zone(Zone(name="goal", x=1, y=0))
    graph.add_connection(Connection(a="start", b="goal"))
    path = DijkstraPathFinder().find(graph, "start", "goal")
    assert path.zones == ("start", "goal")
    assert path.cost == 1


def test_dijkstra_uses_zone_enter_costs() -> None:
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0))
    graph.add_zone(Zone(name="slow", x=1, y=0, type=ZoneType.RESTRICTED))
    graph.add_zone(Zone(name="goal", x=2, y=0))
    graph.add_connection(Connection(a="start", b="slow"))
    graph.add_connection(Connection(a="slow", b="goal"))
    path = DijkstraPathFinder().find(graph, "start", "goal")
    assert path.zones == ("start", "slow", "goal")
    # restricted = 2 turns, normal = 1 turn
    assert path.cost == 3


def test_dijkstra_start_equals_goal() -> None:
    assert DijkstraPathFinder().find(_linear_graph(), "start", "start").cost == 0


def test_dijkstra_unknown_zone_raises() -> None:
    with pytest.raises(KeyError):
        DijkstraPathFinder().find(_linear_graph(), "ghost", "goal")


def test_dijkstra_unreachable_goal_raises() -> None:
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0))
    graph.add_zone(Zone(name="island", x=5, y=5))
    with pytest.raises(ValueError):
        DijkstraPathFinder().find(graph, "start", "island")


def test_dijkstra_on_canonical_easy_01_map() -> None:
    parsed = parse_map(LINKS_EASY_01)
    path = DijkstraPathFinder().find(parsed.graph, parsed.start, parsed.end)
    assert path.zones == ("start", "waypoint1", "waypoint2", "goal")
    assert path.cost == 3


def test_dijkstra_distances_to_returns_cost_to_goal() -> None:
    distances = DijkstraPathFinder().distances_to(_linear_graph(), "goal")
    assert distances["goal"] == 0
    assert distances["hub"] == 1
    assert distances["start"] == 2


def test_dijkstra_distances_to_single_zone() -> None:
    distances = DijkstraPathFinder().distances_to(_linear_graph(), "hub")
    assert distances["hub"] == 0
    assert distances["start"] == 1
    assert distances["goal"] == 1


def _asymmetric_graph() -> Graph:
    """Two start->goal routes: via `slow` (RESTRICTED) and via `a`->`b` (all NORMAL)."""
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


def test_dijkstra_distances_to_asymmetric_costs() -> None:
    """Entering `slow` costs 2 but leaving it costs 1: charge by destination, not origin."""
    distances = DijkstraPathFinder().distances_to(_asymmetric_graph(), "goal")
    assert distances["slow"] == 1  # slow -> goal enters goal (NORMAL) = 1
    assert distances["b"] == 1  # b -> goal enters goal (NORMAL) = 1
    assert distances["a"] == 2  # a -> b -> goal = 1 + 1
    assert distances["start"] == 3  # start -> slow -> goal = 2 + 1


def test_dijkstra_distances_to_matches_forward_find() -> None:
    """Property: the reverse table equals the forward cost for every zone."""
    finder = DijkstraPathFinder()
    graph = _asymmetric_graph()
    distances = finder.distances_to(graph, "goal")
    for zone in distances:
        assert distances[zone] == finder.find(graph, zone, "goal").cost


def test_astar_optimal_with_asymmetric_costs() -> None:
    """With the corrected heuristic, A* must match Dijkstra on destination-charged costs."""
    graph = _asymmetric_graph()
    dijkstra = DijkstraPathFinder()
    via_astar = AStarPathFinder(dijkstra).find(graph, "start", "goal")
    assert via_astar == dijkstra.find(graph, "start", "goal")


def test_astar_returns_same_path_as_dijkstra() -> None:
    graph = _linear_graph()
    via_dijkstra = DijkstraPathFinder().find(graph, "start", "goal")
    via_astar = AStarPathFinder(DijkstraPathFinder()).find(graph, "start", "goal")
    assert via_astar == via_dijkstra


def test_astar_ignores_blocked_neighbours() -> None:
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0))
    graph.add_zone(Zone(name="wall", x=1, y=0, type=ZoneType.BLOCKED))
    graph.add_zone(Zone(name="goal", x=2, y=0))
    graph.add_connection(Connection(a="start", b="wall"))
    graph.add_connection(Connection(a="wall", b="goal"))
    finder = AStarPathFinder(DijkstraPathFinder())
    with pytest.raises(ValueError):
        finder.find(graph, "start", "goal")


def test_pathfinder_is_interface() -> None:
    finder: PathFinder = DijkstraPathFinder()
    assert isinstance(finder, PathFinder)
