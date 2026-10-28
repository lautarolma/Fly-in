"""Zone domain entity: a graph vertex with a type, capacity and color."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ZoneType(Enum):
    """Kind of zone; determines the turn cost of entering it (REQ-ZONE-1)."""

    NORMAL = "normal"
    PRIORITY = "priority"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


@dataclass(slots=True, frozen=True)
class Zone:
    """A named vertex with integer coordinates, a type, capacity and color.

    `cap` is `None` for the uncapped `start_hub`/`end_hub`; otherwise it is the positive
    `max_drones` value (default 1). Immutability makes zones hashable and reproducible.
    """

    name: str
    x: int
    y: int
    type: ZoneType = ZoneType.NORMAL
    cap: int | None = 1
    color: str | None = None
