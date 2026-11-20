"""Drone entity and its finite state machine (REQ-SIM-1)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DroneState(Enum):
    """The three phases of a drone's life in the simulation."""

    WAITING = "waiting"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


@dataclass(slots=True)
class Drone:
    """A drone: immutable route, O(1) cursor and explicit transit state (F3.1)."""

    id: str
    route: tuple[str, ...] = ()
    waypoint_index: int = 0
    state: DroneState = DroneState.WAITING
    target: str | None = None
    transit_turns_left: int = 0

    @property
    def current_zone(self) -> str:
        """Zone occupied at the current waypoint."""
        return self.route[self.waypoint_index]

    @property
    def next_zone(self) -> str | None:
        """Next waypoint, or None when the route is exhausted."""
        index = self.waypoint_index + 1
        if index >= len(self.route):
            return None
        return self.route[index]

    @property
    def route_exhausted(self) -> bool:
        """True when there is no waypoint after the cursor."""
        return self.next_zone is None

    @property
    def is_delivered(self) -> bool:
        """True only for the DELIVERED state, not for an unassigned drone."""
        return self.state is DroneState.DELIVERED


def make_fleet(nb_drones: int, start: str) -> list[Drone]:
    """Create `nb_drones` idle drones D1..DN at `start`, fresh on every call."""
    return [Drone(id=f"D{i}", route=(start,)) for i in range(1, nb_drones + 1)]
