"""Per-turn capacity reservations for zones and connections (F6.1)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReservationTable:
    """Tracks occupancy of `(zone, turn)` and `(connection-key, turn)` slots."""

    zone_slots: dict[tuple[str, int], int] = field(default_factory=dict)
    link_slots: dict[tuple[tuple[str, str], int], int] = field(default_factory=dict)

    def reserve_zone(self, zone: str, turn: int) -> None:
        """Reserve one slot in `zone` for `turn`."""
        raise NotImplementedError

    def reserve_link(self, key: tuple[str, str], turn: int) -> None:
        """Reserve one slot on the connection `key` for `turn`."""
        raise NotImplementedError
