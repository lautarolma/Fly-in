"""Assigns drones to routes: single-route helper (F3.6), ETA-greedy (F5.5)."""

from __future__ import annotations

from dataclasses import replace

from flyin.domain.drone import Drone, DroneState
from flyin.pathfinding.base import Path


def assign_single_route(drones: list[Drone], route: Path) -> list[Drone]:
    """F3.6 / Propuesta A: give every drone the same immutable shortest route.

    Pure function: the input fleet is untouched and fresh `Drone` objects come back
    with the cursor, state and transit fields reset for a new simulation.
    """
    return [
        replace(
            drone,
            route=route.zones,
            waypoint_index=0,
            state=DroneState.WAITING,
            target=None,
            transit_turns_left=0,
        )
        for drone in drones
    ]


class Allocator:
    """Greedy ETA assignment of drones to a chosen set of routes."""

    def assign(self, n_drones: int, routes: list[Path]) -> list[Path]:
        """Return one route per drone, minimizing the estimated makespan."""
        raise NotImplementedError
