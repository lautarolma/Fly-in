"""Assigns drones to routes (ETA-greedy) before simulation (F5.5)."""

from __future__ import annotations

from flyin.pathfinding.base import Path


class Allocator:
    """Greedy ETA assignment of drones to a chosen set of routes."""

    def assign(self, n_drones: int, routes: list[Path]) -> list[Path]:
        """Return one route per drone, minimizing the estimated makespan."""
        raise NotImplementedError
