"""Per-turn capacity reservations for zones and connections (F6.1)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

LinkKey = tuple[str, str]


@dataclass(slots=True)
class ReservationTable:
    """Ledger of committed slots; it enforces no policy and knows no graph.

    `zone_slots` may be released (leavers free capacity in the same turn), but
    `link_slots` is write-once: entries are added at departure and never removed,
    so the whole transit window stays reserved (I11 / D2b).
    """

    zone_slots: dict[tuple[str, int], int] = field(default_factory=dict)
    link_slots: dict[tuple[LinkKey, int], int] = field(default_factory=dict)
    pending_arrivals: dict[str, int] = field(default_factory=dict)
    prune_link_history: bool = True

    # --- zone slots -------------------------------------------------
    def zone_usage(self, zone: str, turn: int) -> int:
        """Committed drones in `zone` at `turn` (0 when absent)."""
        return self.zone_slots.get((zone, turn), 0)

    def reserve_zone(self, zone: str, turn: int) -> None:
        """Occupy one slot in `zone` for `turn`."""
        self.zone_slots[(zone, turn)] = self.zone_usage(zone, turn) + 1

    def release_zone(self, zone: str, turn: int) -> None:
        """Free one slot in `zone` for `turn`; a leaver frees capacity at once."""
        usage = self.zone_usage(zone, turn)
        if usage == 0:
            raise ValueError(f"cannot release unreserved zone {zone!r} at turn {turn}")
        if usage == 1:
            del self.zone_slots[(zone, turn)]
        else:
            self.zone_slots[(zone, turn)] = usage - 1

    def can_reserve_zone(
        self,
        zone: str,
        turn: int,
        cap: int | None,
        *,
        include_pending: bool = False,
    ) -> bool:
        """Whether another drone may enter `zone`; `cap=None` means uncapped hub."""
        if cap is None:
            return True
        used = self.zone_usage(zone, turn)
        if include_pending:
            used += self.pending(zone)
        return used < cap

    # --- link slots -------------------------------------------------
    def link_usage(self, key: LinkKey, turn: int) -> int:
        """Committed slots on physical link `key` at `turn` (0 when absent)."""
        return self.link_slots.get((key, turn), 0)

    def can_reserve_link(self, key: LinkKey, turns: Sequence[int], cap: int) -> bool:
        """Whether every turn of the transit window still has spare capacity."""
        return all(self.link_usage(key, turn) < cap for turn in turns)

    def reserve_link(self, key: LinkKey, turn: int) -> None:
        """Add one committed slot. Never decremented: write-once (I11)."""
        self.link_slots[(key, turn)] = self.link_usage(key, turn) + 1

    def reserve_link_window(
        self, key: LinkKey, turns: Sequence[int], cap: int
    ) -> bool:
        """Atomically check the whole window, then reserve all of it."""
        if not self.can_reserve_link(key, turns, cap):
            return False
        for turn in turns:
            self.reserve_link(key, turn)
        return True

    # --- pending arrivals -------------------------------------------
    def pending(self, zone: str) -> int:
        """Forced landings promised for the next turn (horizon 1)."""
        return self.pending_arrivals.get(zone, 0)

    def add_pending_arrival(self, zone: str) -> None:
        """Promise a landing slot in `zone` at t+1 without occupying it yet."""
        self.pending_arrivals[zone] = self.pending(zone) + 1

    def consume_pending_arrival(self, zone: str) -> None:
        """Turn a promised landing into a physical occupancy at P0."""
        remaining = self.pending(zone) - 1
        if remaining < 0:
            raise ValueError(f"no pending arrival for {zone!r}")
        if remaining == 0:
            del self.pending_arrivals[zone]
        else:
            self.pending_arrivals[zone] = remaining

    # --- maintenance -------------------------------------------------
    def close_turn(self, turn: int) -> None:
        """Prune link slots older than `turn - 1` in production mode."""
        if not self.prune_link_history:
            return
        cutoff = turn - 1
        stale = [slot for slot in self.link_slots if slot[1] < cutoff]
        for slot in stale:
            del self.link_slots[slot]
