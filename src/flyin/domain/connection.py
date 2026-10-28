"""Connection domain entity: a bidirectional, capacitated edge (REQ-CONN-1)."""

from __future__ import annotations

from dataclasses import dataclass


def connection_key(a: str, b: str) -> tuple[str, str]:
    """Return the canonical, order-independent key for a connection.

    `a-b` and `b-a` map to the same key, so they are the same connection.
    """
    return (a, b) if a <= b else (b, a)


@dataclass(slots=True, frozen=True)
class Connection:
    """A bidirectional connection between two zones with a maximum link capacity."""

    a: str
    b: str
    cap: int = 1

    @property
    def key(self) -> tuple[str, str]:
        """Canonical key used to index this connection."""
        return connection_key(self.a, self.b)
