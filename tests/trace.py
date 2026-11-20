"""Test-only re-derivation of per-turn capacity from the official output lines.

This is deliberately NOT production code and NOT the F7 validator: it lives in
`tests/` and no module under `src/` may import it. It exists so F3.5 can assert
the capacity invariants (REQ-CAP-1) against the emitted trace instead of trusting
the very `ReservationTable` the simulator uses.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from flyin.domain.connection import connection_key
from flyin.domain.graph import Graph
from flyin.domain.zone import ZoneType


def assert_trace_respects_caps(
    graph: Graph,
    lines: list[str],
    *,
    start: str,
    drone_ids: Sequence[str],
) -> dict[str, str]:
    """Re-derive zone/link occupancy from `lines`; return final drone positions.

    Tokens are `D<id>-<zone>` (arrival or normal move) and
    `D<id>-<origin>-<destination>` (departure toward a restricted zone, D1).
    A restricted departure occupies the link at turns `t` and `t+1` (D2b) and
    forces a landing token at `t+1` (REQ-TRANSIT-1).

    Raises `AssertionError` on an empty line, a turn prefix, an unknown drone or
    zone, a missing forced landing, a zone over `cap` or a link over `cap`.
    """
    positions: dict[str, str] = {drone_id: start for drone_id in drone_ids}
    pending_landings: dict[str, tuple[str, str]] = {}
    link_usage: dict[tuple[tuple[str, str], int], int] = defaultdict(int)

    for turn, line in enumerate(lines, start=1):
        assert line, f"empty line at turn {turn}"
        assert not line.startswith("turn "), f"turn prefix at turn {turn}"

        departures: dict[str, tuple[str, str]] = {}
        landed: set[str] = set()

        for token in line.split():
            parts = token.split("-")
            assert len(parts) in (2, 3), f"bad token {token!r} at turn {turn}"
            drone_id = parts[0]
            assert drone_id in positions, f"unknown drone {drone_id!r}"

            if len(parts) == 3:
                origin, destination = parts[1], parts[2]
                assert destination in graph.zones, f"unknown zone {destination!r}"
                assert (
                    graph.zones[destination].type is ZoneType.RESTRICTED
                ), f"transit token to non-restricted {destination!r}"
                if drone_id in pending_landings:
                    # It landed earlier in this same line, then took off again.
                    assert drone_id in landed, f"{drone_id} skipped its landing"
                    pending_landings.pop(drone_id)
                assert positions[drone_id] == origin, (
                    f"{drone_id} departs from {origin!r} but was at "
                    f"{positions[drone_id]!r} at turn {turn}"
                )
                departures[drone_id] = (origin, destination)
                key = connection_key(origin, destination)
                link_usage[(key, turn)] += 1
                link_usage[(key, turn + 1)] += 1
                continue

            destination = parts[1]
            assert destination in graph.zones, f"unknown zone {destination!r}"
            if drone_id in pending_landings:
                promised = pending_landings.pop(drone_id)[1]
                assert promised == destination, (
                    f"{drone_id} landed in {destination!r}, promised {promised!r}"
                )
                landed.add(drone_id)
            else:
                origin = positions[drone_id]
                assert destination in graph.neighbors(origin), (
                    f"{drone_id}: {origin!r} and {destination!r} are not connected"
                )
                key = connection_key(origin, destination)
                link_usage[(key, turn)] += 1
            positions[drone_id] = destination

        assert not pending_landings, f"forced landing missing at turn {turn}"

        occupancy: dict[str, int] = defaultdict(int)
        for drone_id, zone in positions.items():
            if drone_id not in departures:
                occupancy[zone] += 1
        for zone, used in occupancy.items():
            cap = graph.zones[zone].cap
            assert cap is None or used <= cap, (
                f"zone {zone!r} over capacity at turn {turn}: {used} > {cap}"
            )

        for (key, slot_turn), used in link_usage.items():
            if slot_turn != turn:
                continue
            connection = graph.connection(key[0], key[1])
            assert used <= connection.cap, (
                f"link {key} over capacity at turn {turn}: {used} > {connection.cap}"
            )

        pending_landings = departures

    assert not pending_landings, "trace ends with a drone still in transit"
    return dict(positions)
