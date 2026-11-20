"""Dijkstra pathfinder over vertex-weighted zone costs (F2.2 / F2.3)."""

from __future__ import annotations

import heapq
from collections.abc import Mapping

from flyin.domain.graph import Graph
from flyin.pathfinding.base import Path, PathFinder


class DijkstraPathFinder(PathFinder):
    """Exact shortest-path search using a `heapq` priority queue.

    `best` stores the lowest known cost for each zone. The `heap` stores
    pending zones ordered by their accumulated cost. Each extracted zone
    may generate new candidate costs for its neighbors. A candidate that
    does not improve the value already stored in `best` is ignored.

    When `goal` is extracted from the heap, its cost is minimal among all
    pending candidates, so the search can stop immediately.

    An optional mapping of extra zone costs lets callers steer subsequent
    searches (F5.1) without changing the domain objects or the base weights.
    """

    def __init__(self, penalties: Mapping[str, int] | None = None) -> None:
        """Store a read-only view of the optional per-zone penalties."""
        self._penalties: Mapping[str, int] = (
            penalties if penalties is not None else {}
        )

    def _weight(self, graph: Graph, zone: str) -> int | None:
        """Return the base enter cost of `zone` plus its accumulated penalty."""
        base = graph.zones[zone].type.enter_cost
        if base is None:
            return None
        return base + self._penalties.get(zone, 0)

    def find(self, graph: Graph, start: str, goal: str) -> Path:
        """Return the minimum-cost path from `start` to `goal` in `graph`."""
        if start not in graph.zones or goal not in graph.zones:
            raise KeyError(f"unknown zone: start={start!r} goal={goal!r}")
        if start == goal:
            return Path(zones=(start,), cost=0)

        best: dict[str, int] = {start: 0}
        parent: dict[str, str] = {}
        heap: list[tuple[int, str]] = [(0, start)]
        while heap:
            distance, node = heapq.heappop(heap)
            if distance > best[node]:
                continue
            if node == goal:
                break
            for neighbor in graph.neighbors(node):
                weight = self._weight(graph, neighbor)
                if weight is None:
                    continue
                candidate = distance + weight
                if neighbor not in best or candidate < best[neighbor]:
                    best[neighbor] = candidate
                    parent[neighbor] = node
                    heapq.heappush(heap, (candidate, neighbor))

        if goal not in best:
            raise ValueError(f"goal {goal!r} is unreachable from start {start!r}")
        zones: list[str] = [goal]
        node = goal
        while node != start:
            node = parent[node]
            zones.append(node)
        zones.reverse()
        return Path(zones=tuple(zones), cost=best[goal])

    def distances_to(self, graph: Graph, goal: str) -> dict[str, int]:
        """Reverse Dijkstra: cost from every zone to `goal` (F2.3).

        Zone costs are charged by destination, so `a->b` and `b->a` may differ.
        Relaxing the reversed edge `neighbor -> node` must therefore charge
        `enter_cost(node)`, not `enter_cost(neighbor)`.
        """
        if goal not in graph.zones:
            raise KeyError(f"unknown zone: goal={goal!r}")
        best: dict[str, int] = {goal: 0}
        heap: list[tuple[int, str]] = [(0, goal)]
        while heap:
            distance, node = heapq.heappop(heap)
            if distance > best[node]:
                continue
            weight = self._weight(graph, node)
            if weight is None:
                continue
            for neighbor in graph.neighbors(node):
                candidate = distance + weight
                if neighbor not in best or candidate < best[neighbor]:
                    best[neighbor] = candidate
                    heapq.heappush(heap, (candidate, neighbor))
        return best
