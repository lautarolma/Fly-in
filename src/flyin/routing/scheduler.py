"""Routing policy: choose the route subset and hand one route to each drone (F5/F6).

The `Scheduler` is the single owner of the *policy* dimension:

- which subset of candidate routes to use (`select_routes`, F5.4);
- which drone walks which route (`Allocator`, F5.5);
- the fleet-level bound of the chosen plan (`fleet_bound`, F5.3).

It delegates the *mechanism* to `RouteBuilder` (how candidates are generated with
the +delta penalty), the *judgement* to `MakespanEstimator` (the bound formula)
and the *execution* to `Simulation` (the per-turn arbiter). It never advances the
clock: that is `Simulation`'s job.
"""

from __future__ import annotations

from itertools import combinations

from flyin.domain.drone import Drone, make_fleet
from flyin.domain.graph import Graph
from flyin.pathfinding.base import Path
from flyin.routing.allocator import Allocator, assign_routes
from flyin.routing.estimator import MakespanEstimator, bottleneck_capacity
from flyin.routing.route_builder import MAX_ROUTES, RouteBuilder


class Scheduler:
    """Owns the routing policy: route subset, per-drone assignment and plan bound."""

    def __init__(self, k: int = 4, penalty: int = 1) -> None:
        self._k = k
        self._builder = RouteBuilder(penalty)
        self._estimator = MakespanEstimator()
        self._allocator = Allocator()

    def plan(
        self, graph: Graph, start: str, end: str, nb_drones: int
    ) -> list[Drone]:
        """Return a fleet with one route per drone, chosen by the F5 policy.

        Pipeline: `RouteBuilder` (mechanism) -> `select_routes` (policy) ->
        `Allocator` (assignment) -> `assign_routes` (apply the vector). The
        caller only supplies the map facts; it never picks `k` or the split.
        """
        routes = self._builder.build_for_fleet(graph, start, end, self._k, nb_drones)
        chosen = self.select_routes(graph, routes, nb_drones)
        assignment = self._allocator.assign(graph, chosen, nb_drones)
        return assign_routes(make_fleet(nb_drones, start), assignment)

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
                bound = self._estimator.estimate(
                    [routes[index].cost for index in indices],
                    loads,
                    [capacities[index] for index in indices],
                )
                candidate = (bound, size, indices)
                if best is None or candidate < best:
                    best = candidate
                    chosen = indices
        return [routes[index] for index in chosen]

    def fleet_bound(
        self, graph: Graph, routes: list[Path], nb_drones: int
    ) -> int:
        """Return the makespan lower bound for the whole fleet over `routes`.

        Chooses the admissible subset with the lowest bound (`select_routes`)
        and returns that bound. This is the fleet-level expression of the
        structural bound `makespan >= c + ceil(N / cap) - 1`, i.e. the number
        the allocator acts on and the number compared against the measured
        makespan. Returns 0 when there is nothing to assign.
        """
        chosen = self.select_routes(graph, routes, nb_drones)
        if not chosen:
            return 0
        costs = [route.cost for route in chosen]
        loads = self._balanced_loads(nb_drones, len(chosen))
        caps = [bottleneck_capacity(graph, route) for route in chosen]
        return self._estimator.estimate(costs, loads, caps)

    @staticmethod
    def _balanced_loads(nb_drones: int, route_count: int) -> list[int]:
        """Split the fleet, giving the remainder to the first routes."""
        base, extra = divmod(nb_drones, route_count)
        return [base + (1 if index < extra else 0) for index in range(route_count)]
