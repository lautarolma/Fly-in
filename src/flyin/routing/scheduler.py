"""Routing policy: choose the route subset and hand one route to each drone (F5/F6).

The `Scheduler` is the single owner of the *policy* dimension:

- which subset of candidate routes to use (`select_routes`, F5.4);
- which drone walks which route (`Allocator`, F5.5);
- the fleet-level bound of the chosen plan (`fleet_bound`, F5.3);
- the shortest subset that actually completes (`plan_validated`, F6.4).

It delegates the *mechanism* to `RouteBuilder` (how candidates are generated with
the +delta penalty), the *judgement* to `MakespanEstimator` (the bound formula)
and the *execution* to `Simulation` (the per-turn arbiter, also used as the F6.4
validation oracle). It never advances the clock itself: `Simulation` does.
"""

from __future__ import annotations

from itertools import combinations
from typing import NamedTuple

from flyin.domain.drone import Drone, make_fleet
from flyin.domain.graph import Graph
from flyin.pathfinding.base import Path
from flyin.routing.allocator import Allocator, assign_routes
from flyin.routing.estimator import MakespanEstimator, bottleneck_capacity
from flyin.routing.route_builder import MAX_ROUTES, RouteBuilder
from flyin.simulation.simulator import DeadlockError, Simulation


class ValidatedPlan(NamedTuple):
    """Fresh unsimulated fleet plus the official lines of the winning attempt."""

    fleet: list[Drone]
    lines: list[str]


class Scheduler:
    """Owns the routing policy: subset, assignment, bound and validated choice."""

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

    def plan_validated(
        self, graph: Graph, start: str, end: str, nb_drones: int
    ) -> ValidatedPlan:
        """Return the valid schedule that finishes in the fewest turns (F6.4).

        Every non-empty subset of candidates is tried once, in the deterministic
        order of `select_routes`. `Simulation` runs each attempt with no visual
        observer: a `DeadlockError` only means "skip this subset", never a printed
        line or a rendered turn. The winner is the attempt with the shortest line
        list; ties keep the earlier subset. A fresh fleet is returned so the CLI
        can simulate it again with the renderer attached. If no subset completes,
        the last deadlock is re-raised as a single `DeadlockError`.
        """
        if nb_drones < 0:
            raise ValueError("nb_drones must be >= 0")
        if nb_drones == 0:
            return ValidatedPlan(fleet=[], lines=[])
        routes = self._builder.build_for_fleet(graph, start, end, self._k, nb_drones)
        if not routes:
            raise ValueError("cannot assign drones without routes")
        subsets = self._ranked_subsets(graph, routes, nb_drones)
        best: tuple[int, list[str]] | None = None
        best_assignment: list[Path] = []
        last_error: DeadlockError | None = None
        for _rank, subset in subsets:
            assignment = self._allocator.assign(graph, subset, nb_drones)
            fleet = assign_routes(make_fleet(nb_drones, start), assignment)
            try:
                lines = Simulation(graph, fleet, end).run()
            except DeadlockError as exc:
                last_error = exc
                continue
            # A route may end before the goal; that "delivers" the drone in the
            # simulator but is not a valid schedule for the map.
            if not all(drone.current_zone == end for drone in fleet):
                continue
            # Strict '<' keeps the earlier ranked subset on a turns tie.
            if best is None or len(lines) < best[0]:
                best = (len(lines), lines)
                best_assignment = assignment
        if best is None:
            if last_error is not None:
                raise DeadlockError(
                    "no route selection produced a valid schedule: "
                    f"{last_error}"
                ) from last_error
            raise DeadlockError(f"no route selection delivers the fleet to {end!r}")
        return ValidatedPlan(
            fleet=assign_routes(make_fleet(nb_drones, start), best_assignment),
            lines=best[1],
        )

    def select_routes(
        self, graph: Graph, routes: list[Path], nb_drones: int
    ) -> list[Path]:
        """Return the subset with the lowest estimated makespan (F5.4).

        All non-empty subsets of the bounded candidate set are enumerated.
        Within a subset the fleet is split as evenly as possible, with the
        remainder going to the cheapest routes first. Ties prefer fewer routes
        and then the earlier candidates, so the result is deterministic.
        """
        ranked = self._ranked_subsets(graph, routes, nb_drones)
        if not ranked:
            return []
        return ranked[0][1]

    def _ranked_subsets(
        self, graph: Graph, routes: list[Path], nb_drones: int
    ) -> list[tuple[tuple[int, int, tuple[int, ...]], list[Path]]]:
        """Return every non-empty subset, ordered as `select_routes` ranks them.

        F6.4 reuses the F5.4 order (bound, route count, candidate indices) so a
        retry never changes the deterministic preference that produced the first
        attempt. Each item is `(rank, subset)`, ready for silent simulation.
        """
        if nb_drones < 0:
            raise ValueError("nb_drones must be >= 0")
        if len(routes) > MAX_ROUTES:
            raise ValueError(f"at most {MAX_ROUTES} candidate routes are allowed")
        if nb_drones == 0 or not routes:
            return []

        capacities = [bottleneck_capacity(graph, route) for route in routes]
        ranked: list[tuple[tuple[int, int, tuple[int, ...]], list[Path]]] = []
        for size in range(1, len(routes) + 1):
            for indices in combinations(range(len(routes)), size):
                loads = self._balanced_loads(nb_drones, size)
                bound = self._estimator.estimate(
                    [routes[index].cost for index in indices],
                    loads,
                    [capacities[index] for index in indices],
                )
                ranked.append(
                    ((bound, size, indices), [routes[index] for index in indices])
                )
        ranked.sort(key=lambda item: item[0])
        return ranked

    def fleet_bound(
        self, graph: Graph, routes: list[Path], nb_drones: int
    ) -> int:
        """Return a lower-bound estimate of turns for the fleet to arrive.

        Selects routes for the fleet, balances the drones across them, and
        passes each route's cost, assigned drone count, and bottleneck capacity
        to the estimator. Returns 0 if there are no routes to assign drones to.
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
        """Split the fleet, giving the remainder to the first routes(Euclidean division)."""
        base, extra = divmod(nb_drones, route_count)
        return [base + (1 if index < extra else 0) for index in range(route_count)]
