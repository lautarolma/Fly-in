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


def route_bound(cost: int, load: int, cap: int) -> int:
    """Return the F5.3 cota of a single route: `cost + ceil(load / cap) - 1`.

    This is the only place the formula lives: `estimate` maximises it across
    routes and the F5.5 allocator evaluates it one drone ahead (`load + 1`) to
    rank candidate routes. An empty route contributes nothing, so `load == 0`
    returns 0 instead of the meaningless `cost - 1` and callers can take the
    max over every route without filtering.
    """
    if cost < 0:
        raise ValueError("route cost must be >= 0")
    if load < 0:
        raise ValueError("load must be >= 0")
    if cap < 1:
        raise ValueError("capacity must be >= 1")
    if load == 0:
        return 0
    return cost + (load + cap - 1) // cap - 1


class MakespanEstimator:
    """Admissible lower bounds over a candidate set of routes."""

    def estimate(
        self,
        route_costs: list[int],
        loads: list[int],
        capacities: list[int],
    ) -> int:
        """Return `max(route_bound(cost_i, load_i, cap_i))`.

        With `cap_i = 1` this is the lem-in bound. Larger capacities let
        drones enter in parallel, so the injection term shrinks. Routes with
        no assigned drones contribute nothing. Never simulates.
        """
        if not len(route_costs) == len(loads) == len(capacities):
            raise ValueError("route_costs, loads and capacities must align")

        return max(
            (
                route_bound(cost, load, cap)
                for cost, load, cap in zip(route_costs, loads, capacities)
            ),
            default=0,
        )

    def fleet_bound(self, graph: Graph, routes: list[Path], nb_drones: int) -> int:
        """Return the makespan lower bound for the whole fleet over `routes`.

        Chooses the admissible subset with the lowest bound (`select_routes`) and
        returns that bound. This is the fleet-level expression of the structural
        bound `makespan >= c + ceil(N / cap) - 1`, i.e. the number the allocator
        acts on and the number compared against the measured makespan.

        Returns 0 when there is nothing to assign (no drones or no candidates).
        """
        chosen = self.select_routes(graph, routes, nb_drones)
        if not chosen:
            return 0
        costs = [route.cost for route in chosen]
        loads = self._balanced_loads(nb_drones, len(chosen))
        caps = [bottleneck_capacity(graph, route) for route in chosen]
        return self.estimate(costs, loads, caps)

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
