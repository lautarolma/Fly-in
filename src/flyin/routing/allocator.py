"""Assigns drones to routes: single-route helper (F3.6), ETA-greedy (F5.5)."""

from __future__ import annotations

from dataclasses import replace

from flyin.domain.drone import Drone, DroneState
from flyin.domain.graph import Graph
from flyin.pathfinding.base import Path
from flyin.routing.estimator import bottleneck_capacity, route_bound


def _restart(drone: Drone, route: Path) -> Drone:
    """Return a fresh copy of `drone` walking `route` from its first waypoint."""
    return replace(
        drone,
        route=route.zones,
        waypoint_index=0,
        state=DroneState.WAITING,
        target=None,
        transit_turns_left=0,
    )


def assign_single_route(drones: list[Drone], route: Path) -> list[Drone]:
    """F3.6 / Propuesta A: give every drone the same immutable shortest route.

    Pure function: the input fleet is untouched and fresh `Drone` objects come back
    with the cursor, state and transit fields reset for a new simulation.
    """
    return [_restart(drone, route) for drone in drones]


def assign_routes(drones: list[Drone], assignment: list[Path]) -> list[Drone]:
    """Apply a per-drone route vector (F5.5): one route per drone, in order.

    Same purity contract as `assign_single_route`; the vector is what
    `Allocator.assign` planned. Raises when the vector does not match the fleet,
    so a misaligned plan never silently drops a drone.
    """
    if len(drones) != len(assignment):
        raise ValueError("assignment must hold exactly one route per drone")
    return [_restart(drone, route) for drone, route in zip(drones, assignment)]


class Allocator:
    """Greedy ETA assignment of drones to a chosen set of routes."""

    def assign(
        self, graph: Graph, routes: list[Path], nb_drones: int
    ) -> list[Path]:
        """Return one route per drone, minimizing the estimated makespan (F5.5).

        Each drone joins the route whose F5.3 cota is the smallest *after*
        accepting it: `route_bound(cost, load + 1, cap)`, with `cap` the route's
        bottleneck. Ties fall back to the route carrying fewer drones and then
        to candidate order, so the split is deterministic and lands on the
        balanced loads `MakespanEstimator.select_routes` scored subsets with.
        """
        if nb_drones < 0:
            raise ValueError("nb_drones must be >= 0")
        if nb_drones == 0:
            return []
        if not routes:
            raise ValueError("cannot assign drones without routes")

        capacities = [bottleneck_capacity(graph, route) for route in routes]
        loads = [0] * len(routes)
        assignment: list[Path] = []
        for _ in range(nb_drones):
            # (eta, load, index): the lowest bound wins; an eta tie goes to the
            # emptier route — that split leaves the bound untouched — and then
            # to candidate order, so two runs return the very same vector.
            best = min(
                (
                    route_bound(route.cost, loads[index] + 1, capacities[index]),
                    loads[index],
                    index,
                )
                for index, route in enumerate(routes)
            )[2]
            loads[best] += 1
            assignment.append(routes[best])
        return assignment
