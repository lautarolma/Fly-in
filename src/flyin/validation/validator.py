"""JUEZ 2: independent auditor of a produced schedule (F7.1).

This component re-derives all rules from scratch and shares no logic with the simulator. Input
validation is a different concern and lives in the `parsing` layer.
"""

from __future__ import annotations

from flyin.domain.graph import Graph


class Validator:
    """Re-derives the rules and audits each turn of a schedule."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def check(self, lines: list[str]) -> list[str]:
        """Return the list of rule violations (empty means a valid schedule)."""
        raise NotImplementedError
