"""PathFinder interface and the Path value type (F2.1)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from flyin.domain.graph import Graph


@dataclass(slots=True, frozen=True)
class Path:
    """An ordered list of zone names from start to goal, with its total cost."""

    zones: tuple[str, ...]
    cost: int


class PathFinder(ABC):
    """Interface for shortest-path strategies (Dijkstra, A*, ...).

    Implementations must not know about drones or turns — only the graph and costs.
    """

    @abstractmethod
    def find(self, graph: Graph, start: str, goal: str) -> Path:
        """Return a minimum-cost path from `start` to `goal` in `graph`."""
        raise NotImplementedError
