"""Drone entity and its finite state machine (REQ-SIM-1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DroneState(Enum):
    """The three phases of a drone's life in the simulation."""

    WAITING = "waiting"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


@dataclass(slots=True)
class Drone:
    """A single drone: identity, planned route and current FSM state."""

    id: str
    path: list[str] = field(default_factory=list)
    index: int = 0
    state: DroneState = DroneState.WAITING
