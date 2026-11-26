"""JUEZ 1: estimates the makespan of a route assignment without simulating (F5.3).

This module owns the *judgement*: the bound formula (`route_bound`), the
bottleneck capacity of a route and the fleet expression of the bound. Choosing
which route subset to use is *policy* and lives in `routing/scheduler.py`.
"""

from __future__ import annotations

import sys

from flyin.domain.graph import Graph
from flyin.pathfinding.base import Path

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
        """Estimate the minimum number of turns the fleet could need to finish.

        Args:
            route_costs: Cost of traveling each route.
            loads: Number of drones assigned to each route.
            capacities: Number of drones that can move along each route per
                turn, limited by its narrowest point. Entries with the same
                index describe the same route.

        Returns:
            The highest estimate among the routes. The fleet is not finished
            until the drones on its slowest route arrive. A route with no drones
            adds no time; if there are no routes, this returns 0.

        This is an estimate, not a simulation: it does not move drones turn by
        turn. All three lists must have the same length.
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
