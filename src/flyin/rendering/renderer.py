"""Colored terminal rendering (visual feedback, REQ-VIS-1).

Writes to a stream that is never stdout, so the official per-turn lines stay byte-for-byte clean.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from collections.abc import Sequence
from typing import TextIO

from flyin.domain.drone import Drone, DroneState
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone, ZoneType

_ANSI = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "orange": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "grey": "90",
    "gray": "90",
}

_BY_TYPE = {
    ZoneType.NORMAL: "37",
    ZoneType.PRIORITY: "92",
    ZoneType.RESTRICTED: "31",
    ZoneType.BLOCKED: "90",
}

_RESET = "\033[0m"


def _color(zone: Zone) -> str:
    """Return the ANSI code for `zone`, falling back to its semantic type."""
    if zone.color is not None:
        code = _ANSI.get(zone.color.lower())
        if code is not None:
            return code
    return _BY_TYPE[zone.type]


class Renderer:
    """Renders zones and drones with ANSI colors on a separate stream."""

    def __init__(
        self,
        graph: Graph,
        drones: Sequence[Drone],
        stream: TextIO | None = None,
    ) -> None:
        self.graph = graph
        self.drones = tuple(drones)
        self.stream = stream if stream is not None else sys.stderr

    def render(self, turn: int, line: str = "") -> None:
        """Render the post-turn state: zones, occupants, in-flight drones, official line."""
        print(f"--- turn {turn} ---", file=self.stream)
        occupied: dict[str, list[str]] = defaultdict(list)
        for drone in self.drones:
            if drone.state is not DroneState.IN_TRANSIT:
                occupied[drone.current_zone].append(drone.id)

        for zone in self.graph.zones.values():
            ids = ", ".join(occupied[zone.name]) if occupied[zone.name] else "-"
            print(f"\033[{_color(zone)}m{zone.name}{_RESET} [{ids}]", file=self.stream)

        in_transit = [
            f"{drone.id}->{drone.target}"
            for drone in self.drones
            if drone.state is DroneState.IN_TRANSIT and drone.target is not None
        ]
        if in_transit:
            print(f"in transit: {' '.join(in_transit)}", file=self.stream)
        if line:
            print(f"official: {line}", file=self.stream)
