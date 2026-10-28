"""The navigable graph: zones and their incident connections.

`blocked` zones and their connections are pruned at build time, so this structure only contains
zones a drone may actually occupy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from flyin.domain.connection import Connection
from flyin.domain.zone import Zone


@dataclass(slots=True)
class Graph:
    """Adjacency structure over zones keyed by name."""

    zones: dict[str, Zone] = field(default_factory=dict)
    adj: dict[str, dict[str, Connection]] = field(default_factory=dict)

    def add_zone(self, zone: Zone) -> None:
        """Register a zone (idempotent by name)."""
        self.zones[zone.name] = zone
        self.adj.setdefault(zone.name, {})

    def add_connection(self, connection: Connection) -> None:
        """Register a bidirectional connection between two already-added zones."""
        self.adj.setdefault(connection.a, {})[connection.b] = connection
        self.adj.setdefault(connection.b, {})[connection.a] = connection

    def neighbors(self, name: str) -> list[str]:
        """Return the names of zones directly reachable from `name`."""
        return list(self.adj.get(name, {}))

    def connection(self, a: str, b: str) -> Connection:
        """Return the connection between two adjacent zones, or raise `KeyError`."""
        try:
            return self.adj[a][b]
        except KeyError as exc:
            raise KeyError(f"no connection between {a!r} and {b!r}") from exc
