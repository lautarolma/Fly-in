"""A* pathfinder using the reverse-Dijkstra heuristic (F2.4, optional)."""

from __future__ import annotations

from flyin.domain.graph import Graph
from flyin.pathfinding.base import Path, PathFinder


class AStarPathFinder(PathFinder):
    """A* over the zone-cost graph with `h = dist_to_end` (admissible and consistent)."""

    def find(self, graph: Graph, start: str, goal: str) -> Path:
        """Return a shortest path using A* with the reverse-Dijkstra heuristic."""
        raise NotImplementedError
