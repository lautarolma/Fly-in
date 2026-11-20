"""JUEZ 1: estimates the makespan of a route assignment without simulating (F5.3)."""

from __future__ import annotations

import sys
from itertools import combinations

from flyin.domain.graph import Graph
from flyin.pathfinding.base import Path
from flyin.routing.route_builder import MAX_ROUTES

UNBOUNDED = sys.maxsize


def bottleneck_capacity(graph: Graph, route: Path) -> int:
    """Return the tightest zone/link capacity along `route`.

    Both zones and connections throttle throughput, so the minimum of all of
    them governs how many drones may be injected per turn. Uncapped hubs
    (`cap is None`) are ignored and represented by `UNBOUNDED`.
    """
    caps: list[int] = []
    zones = route.zones
    for zone in zones[1:]:
        cap = graph.zones[zone].cap
        if cap is not None:
            caps.append(cap)
    for origin, destination in zip(zones, zones[1:]):
        caps.append(graph.connection(origin, destination).cap)
    return min(caps) if caps else UNBOUNDED


class MakespanEstimator:
    """Admissible lower bounds over a candidate set of routes."""

    def estimate(
        self,
        route_costs: list[int],
        loads: list[int],
        capacities: list[int],
    ) -> int:
        """Return `max(cost_i + ceil(load_i / cap_i) - 1)`.

        With `cap_i = 1` this is the lem-in bound. Larger capacities let
        drones enter in parallel, so the injection term shrinks. Routes with
        no assigned drones contribute nothing. Never simulates.
        """
        if not len(route_costs) == len(loads) == len(capacities):
            raise ValueError("route_costs, loads and capacities must align")

        bounds: list[int] = []
        for cost, load, cap in zip(route_costs, loads, capacities):
            if cost < 0:
                raise ValueError("route cost must be >= 0")
            if load < 0:
                raise ValueError("load must be >= 0")
            if cap < 1:
                raise ValueError("capacity must be >= 1")
            if load == 0:
                continue
            bounds.append(cost + (load + cap - 1) // cap - 1)
        return max(bounds) if bounds else 0

    def select_routes(
        self, graph: Graph, routes: list[Path], nb_drones: int
    ) -> list[Path]:
        """Return the subset with the lowest estimated makespan (F5.4).

        All non-empty subsets of the bounded candidate set are enumerated.
        Within a subset the fleet is split as evenly as possible, with the
        remainder going to the cheapest routes first. Ties prefer fewer routes
        and then the earlier candidates, so the result is deterministic.
        """
        if nb_drones < 0:
            raise ValueError("nb_drones must be >= 0")
        if len(routes) > MAX_ROUTES:
            raise ValueError(f"at most {MAX_ROUTES} candidate routes are allowed")
        if nb_drones == 0 or not routes:
            return []

        capacities = [bottleneck_capacity(graph, route) for route in routes]
        best: tuple[int, int, tuple[int, ...]] | None = None
        chosen: tuple[int, ...] = ()
        for size in range(1, len(routes) + 1):
            for indices in combinations(range(len(routes)), size):
                loads = self._balanced_loads(nb_drones, size)
                bound = self.estimate(
                    [routes[index].cost for index in indices],
                    loads,
                    [capacities[index] for index in indices],
                )
                candidate = (bound, size, indices)
                if best is None or candidate < best:
                    best = candidate
                    chosen = indices
        return [routes[index] for index in chosen]

    @staticmethod
    def _balanced_loads(nb_drones: int, route_count: int) -> list[int]:
        """Split the fleet, giving the remainder to the first routes."""
        base, extra = divmod(nb_drones, route_count)
        return [base + (1 if index < extra else 0) for index in range(route_count)]
