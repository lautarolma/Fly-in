"""Official output formatting: one line per turn, no turn prefix (REQ-OUT-1, D5)."""

from __future__ import annotations


def format_turn(movements: list[str]) -> str:
    """Join the turn's movement tokens with spaces; omit the turn prefix (D5)."""
    return " ".join(movements)


def move_token(drone_id: str, zone: str) -> str:
    """Movement token for a drone entering a zone: `D<id>-<zone>`."""
    return f"{drone_id}-{zone}"


def transit_token(drone_id: str, origin: str, destination: str) -> str:
    """Transit token toward a restricted zone: `D<id>-<origin>-<destination>` (D1)."""
    return f"{drone_id}-{origin}-{destination}"
