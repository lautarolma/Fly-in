"""Builds the candidate set of k routes used to distribute drones (F5.1/F5.2)."""

from __future__ import annotations

from flyin.domain.graph import Graph
from flyin.pathfinding.base import Path
from flyin.pathfinding.dijkstra import DijkstraPathFinder

MAX_ROUTES = 4


def cap_route_count(k: int, nb_drones: int) -> int:
    """Return the effective route count: `min(k, MAX_ROUTES, nb_drones)`."""
    return max(0, min(k, MAX_ROUTES, nb_drones))


class RouteBuilder:
    """Produces up to `k` distinct candidate routes between two zones."""

    def __init__(self, penalty: int = 1) -> None:
        """Set the positive delta added to a reused zone on each iteration."""
        if penalty < 1:
            raise ValueError("penalty must be at least 1")
        self._penalty = penalty

    def build(self, graph: Graph, start: str, goal: str, k: int) -> list[Path]:
        """Return up to `k` distinct routes, cheapest first.

        Positive penalties (+delta) are accumulated on the *internal* zones of
        each chosen route, so the next search is steered towards another
        corridor. Start and goal belong to every route; penalizing them would
        not discriminate between candidates.
        """
        k = min(k, MAX_ROUTES)
        if k <= 0:
            return []
        if start == goal:
            return [Path(zones=(start,), cost=0)]

        penalties: dict[str, int] = {}
        routes: list[Path] = []
        seen: set[tuple[str, ...]] = set()
        # A route cannot have more vertices than the graph. Bounding the
        # attempts keeps the search finite when no new route can be found.
        max_attempts = k * len(graph.zones) + 1
        for _ in range(max_attempts):
            if len(routes) >= k:
                break
            found = DijkstraPathFinder(penalties).find(graph, start, goal)
            if found.zones in seen:
                self._penalize(penalties, found.zones)
                continue
            seen.add(found.zones)
            routes.append(
                Path(
                    zones=found.zones,
                    cost=self._real_cost(graph, found.zones),
                )
            )
            self._penalize(penalties, found.zones)
        return routes

    def build_for_fleet(
        self, graph: Graph, start: str, goal: str, k: int, nb_drones: int
    ) -> list[Path]:
        """Build routes for a fleet, capping `k` by both 4 and the fleet size."""
        return self.build(graph, start, goal, cap_route_count(k, nb_drones))

    def _penalize(self, penalties: dict[str, int], zones: tuple[str, ...]) -> None:
        """Add +delta to the internal zones of `zones`."""
        for zone in zones[1:-1]:
            penalties[zone] = penalties.get(zone, 0) + self._penalty

    @staticmethod
    def _real_cost(graph: Graph, zones: tuple[str, ...]) -> int:
        """Compute the cost with original weights, without search penalties."""
        total = 0
        for zone in zones[1:]:
            weight = graph.zones[zone].type.enter_cost
            if weight is None:
                raise ValueError(f"unpassable zone in route: {zone!r}")
            total += weight
        return total
