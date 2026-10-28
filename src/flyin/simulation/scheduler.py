"""Assigns drones to routes and enforces per-turn capacity (F6.2/F6.3)."""

from __future__ import annotations

from flyin.domain.drone import Drone
from flyin.domain.graph import Graph
from flyin.pathfinding.base import Path
from flyin.simulation.reservation_table import ReservationTable


class Scheduler:
    """Builds a valid schedule: free leaves, then reserve arrivals."""

    def __init__(self, graph: Graph, table: ReservationTable) -> None:
        self.graph = graph
        self.table = table

    def schedule(self, drones: list[Drone], routes: list[Path]) -> None:
        """Assign routes and per-turn reservations, raising on deadlock."""
        raise NotImplementedError
