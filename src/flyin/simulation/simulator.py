"""The simulation loop: decide → apply → commit, one line per turn (F3.2)."""

from __future__ import annotations

from flyin.domain.drone import Drone
from flyin.domain.graph import Graph
from flyin.simulation.scheduler import Scheduler


class Simulation:
    """Advances discrete turns and emits the official movement lines."""

    def __init__(self, graph: Graph, drones: list[Drone], scheduler: Scheduler) -> None:
        self.graph = graph
        self.drones = drones
        self.scheduler = scheduler

    def run(self) -> list[str]:
        """Simulate until all drones are delivered; return the per-turn lines."""
        raise NotImplementedError
