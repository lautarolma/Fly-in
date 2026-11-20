"""JUEZ 1: estimates the makespan of a route assignment without simulating (F5.3)."""

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
