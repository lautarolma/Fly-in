"""A* pathfinder using the reverse-Dijkstra heuristic (F2.4, optional)."""

from __future__ import annotations

import heapq

from flyin.domain.graph import Graph
from flyin.pathfinding.base import Path, PathFinder
from flyin.pathfinding.dijkstra import DijkstraPathFinder


class AStarPathFinder(PathFinder):
    """A* over the zone-cost graph with `h = dist_to_end` (admissible and consistent)."""

    def __init__(self, dijkstra: DijkstraPathFinder | None = None) -> None:
        """Accept a Dijkstra instance (defaults to a fresh one) for the heuristic."""
        self._dijkstra = dijkstra if dijkstra is not None else DijkstraPathFinder()

    def find(self, graph: Graph, start: str, goal: str) -> Path:
        """Return the shortest path using A* with the reverse-Dijkstra heuristic."""
        if start not in graph.zones or goal not in graph.zones:
            raise KeyError(f"unknown zone: start={start!r} goal={goal!r}")
        if start == goal:
            return Path(zones=(start,), cost=0)

        dist_to_end = self._dijkstra.distances_to(graph, goal)
        start_h = dist_to_end.get(start, 0)

        best: dict[str, int] = {start: 0}
        parent: dict[str, str] = {}
        heap: list[tuple[int, int, str]] = [(start_h, 0, start)]
        while heap:
            _f, g, node = heapq.heappop(heap)
            if g > best[node]:
                continue
            if node == goal:
                break
            for neighbor in graph.neighbors(node):
                weight = graph.zones[neighbor].type.enter_cost
                if weight is None:
                    continue
                candidate = g + weight
                if neighbor not in best or candidate < best[neighbor]:
                    best[neighbor] = candidate
                    parent[neighbor] = node
                    neighbor_h = dist_to_end.get(neighbor)
                    if neighbor_h is None:
                        continue
                    heapq.heappush(heap, (candidate + neighbor_h, candidate, neighbor))

        if goal not in best:
            raise ValueError(f"goal {goal!r} is unreachable from start {start!r}")
        zones: list[str] = [goal]
        node = goal
        while node != start:
            node = parent[node]
            zones.append(node)
        zones.reverse()
        return Path(zones=tuple(zones), cost=best[goal])
