"""Dijkstra pathfinder over vertex-weighted zone costs (F2.2 / F2.3)."""

from __future__ import annotations

from flyin.domain.graph import Graph
from flyin.pathfinding.base import Path, PathFinder


class DijkstraPathFinder(PathFinder):
    """Exact shortest-path search using a `heapq` priority queue."""

    def find(self, graph: Graph, start: str, goal: str) -> Path:
        """Return the minimum-cost path from `start` to `goal`."""
        raise NotImplementedError

    def distances_to(self, graph: Graph, goal: str) -> dict[str, int]:
        """Reverse Dijkstra: cost from every zone to `goal` (tie-break heuristic, F2.3)."""
        raise NotImplementedError
