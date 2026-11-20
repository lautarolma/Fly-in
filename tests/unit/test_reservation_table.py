"""F6.1: per-turn slot ledger, write-once links and pending arrivals."""

from __future__ import annotations

import pytest

from flyin.simulation.reservation_table import LinkKey, ReservationTable

LINK: LinkKey = ("hub", "roof1")


def test_zone_round_trip_and_release_before_reserve() -> None:
    """Una salida libera el cupo antes de que entre otro (REQ-SWAP-1)."""
    table = ReservationTable()
    table.reserve_zone("A", 1)
    assert table.zone_usage("A", 1) == 1
    assert not table.can_reserve_zone("A", 1, 1)
    table.release_zone("A", 1)
    assert table.zone_usage("A", 1) == 0
    assert table.can_reserve_zone("A", 1, 1)


def test_release_unreserved_zone_raises() -> None:
    """Liberar dos veces sería un bug silencioso: mejor fallar."""
    table = ReservationTable()
    with pytest.raises(ValueError, match="unreserved zone"):
        table.release_zone("A", 1)


def test_uncapped_zone_ignores_capacity() -> None:
    """start_hub/end_hub no tienen límite (REQ-CAP-1)."""
    table = ReservationTable()
    table.reserve_zone("end", 1)
    table.reserve_zone("end", 1)
    assert table.zone_usage("end", 1) == 2
    assert table.can_reserve_zone("end", 1, None)


def test_pending_arrival_counts_toward_admission_but_not_occupancy() -> None:
    """La llegada forzada reserva cupo sin ocupar físicamente (I5)."""
    table = ReservationTable()
    table.reserve_zone("roof1", 2)
    table.add_pending_arrival("roof1")
    assert table.zone_usage("roof1", 2) == 1
    assert table.pending("roof1") == 1
    assert not table.can_reserve_zone("roof1", 2, 2, include_pending=True)
    assert table.can_reserve_zone("roof1", 2, 2)


def test_pending_arrival_is_consumed_once() -> None:
    """P0 consume la promesa al aterrizar."""
    table = ReservationTable()
    table.add_pending_arrival("roof1")
    table.add_pending_arrival("roof1")
    assert table.pending("roof1") == 2
    table.consume_pending_arrival("roof1")
    assert table.pending("roof1") == 1
    table.consume_pending_arrival("roof1")
    assert table.pending("roof1") == 0
    assert "roof1" not in table.pending_arrivals
    with pytest.raises(ValueError, match="no pending arrival"):
        table.consume_pending_arrival("roof1")


def test_link_slots_are_write_once() -> None:
    """I11: se escribe al aprobar y nunca se libera (no hay release_link)."""
    table = ReservationTable()
    assert not hasattr(table, "release_link")
    table.reserve_link(LINK, 1)
    table.reserve_link(LINK, 1)
    assert table.link_slots[(LINK, 1)] == 2
    assert table.link_usage(LINK, 1) == 2


def test_link_window_checks_all_slots_before_writing_any() -> None:
    """D2b: si el segundo turno está ocupado, no se reserva ninguno."""
    table = ReservationTable()
    table.reserve_link(LINK, 2)
    assert not table.reserve_link_window(LINK, (1, 2), 1)
    assert table.link_usage(LINK, 1) == 0
    assert table.link_usage(LINK, 2) == 1

    del table.link_slots[(LINK, 2)]
    assert table.reserve_link_window(LINK, (1, 2), 1)
    assert table.link_usage(LINK, 1) == 1
    assert table.link_usage(LINK, 2) == 1


def test_link_window_accepts_cap_two() -> None:
    """Write-once no es bool: con cap=2 el contador puede llegar a 2."""
    table = ReservationTable()
    assert table.reserve_link_window(LINK, (1, 2), 2)
    assert table.reserve_link_window(LINK, (1, 2), 2)
    assert table.link_usage(LINK, 1) == 2
    assert table.link_usage(LINK, 2) == 2
    assert not table.reserve_link_window(LINK, (1, 2), 2)


def test_close_turn_prunes_by_default() -> None:
    """Producción: sólo sobreviven turnos >= t-1."""
    table = ReservationTable()
    for turn in (1, 2, 3):
        table.reserve_link(LINK, turn)
    table.close_turn(3)
    assert table.link_usage(LINK, 1) == 0
    assert table.link_usage(LINK, 2) == 1
    assert table.link_usage(LINK, 3) == 1


def test_close_turn_debug_keeps_full_history() -> None:
    """prune_link_history=False conserva el libro completo para debug."""
    table = ReservationTable(prune_link_history=False)
    for turn in (1, 2, 3):
        table.reserve_link(LINK, turn)
    table.close_turn(3)
    table.close_turn(10)
    assert [table.link_usage(LINK, t) for t in (1, 2, 3)] == [1, 1, 1]
