"""Builds the candidate set of k routes used to distribute drones (F5.1/F5.2)."""

from __future__ import annotations

from flyin.domain.graph import Graph
from flyin.pathfinding.base import Path


class RouteBuilder:
    """Produces up to `k = min(4, nb_drones)` candidate routes."""

    def build(self, graph: Graph, start: str, goal: str, k: int) -> list[Path]:
        """Return up to `k` candidate routes (node-disjoint iterated or penalty +delta)."""
        raise NotImplementedError
