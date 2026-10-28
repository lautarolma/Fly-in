"""JUEZ 1: estimates the makespan of a route assignment without simulating (F5.3)."""

from __future__ import annotations


class MakespanEstimator:
    """Lower/upper bounds over a candidate set of routes."""

    def estimate(self, route_costs: list[int], loads: list[int]) -> int:
        """Return the estimated makespan: max(cost_i + load_i - 1), lem-in style."""
        raise NotImplementedError
