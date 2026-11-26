"""F7 — JUEZ 2: auditoría independiente del schedule (checks, gate y 10 mapas)."""

from __future__ import annotations

from pathlib import Path

import pytest

from flyin.domain.connection import Connection
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone, ZoneType
from flyin.parsing.input_rules import load_map
from flyin.parsing.parser import ParsedMap
from flyin.routing.scheduler import Scheduler
from flyin.validation import ScheduleError, Validator

MAPS_DIR = Path(__file__).resolve().parents[2] / "maps"
ALL_MAPS = sorted(MAPS_DIR.rglob("*.txt"))


def _simple_map() -> ParsedMap:
    """Un corredor start → a → b(restricted) → end, un dron."""
    graph = Graph()
    graph.add_zone(Zone("start", 0, 0, ZoneType.NORMAL, None))
    graph.add_zone(Zone("a", 1, 0, ZoneType.NORMAL, 1))
    graph.add_zone(Zone("b", 2, 0, ZoneType.RESTRICTED, 1))
    graph.add_zone(Zone("end", 3, 0, ZoneType.NORMAL, None))
    graph.add_connection(Connection("start", "a"))
    graph.add_connection(Connection("a", "b"))
    graph.add_connection(Connection("b", "end"))
    return ParsedMap(graph=graph, nb_drones=1, start="start", end="end")


def _swap_map() -> ParsedMap:
    """Dos cupos de 1 en A y B para probar swap y liberación de salidas."""
    graph = Graph()
    graph.add_zone(Zone("start", 0, 0, ZoneType.NORMAL, None))
    graph.add_zone(Zone("A", 1, 0, ZoneType.NORMAL, 1))
    graph.add_zone(Zone("B", 2, 0, ZoneType.NORMAL, 1))
    graph.add_zone(Zone("end", 3, 0, ZoneType.NORMAL, None))
    graph.add_connection(Connection("start", "A"))
    graph.add_connection(Connection("A", "B"))
    graph.add_connection(Connection("B", "end"))
    return ParsedMap(graph=graph, nb_drones=2, start="start", end="end")


def _restricted_shared_map() -> ParsedMap:
    """Dos drones comparten link hacia una zona restricted."""
    graph = Graph()
    graph.add_zone(Zone("start", 0, 0, ZoneType.NORMAL, None))
    graph.add_zone(Zone("r", 1, 0, ZoneType.RESTRICTED, 1))
    graph.add_zone(Zone("end", 2, 0, ZoneType.NORMAL, None))
    graph.add_connection(Connection("start", "r"))
    graph.add_connection(Connection("r", "end"))
    return ParsedMap(graph=graph, nb_drones=2, start="start", end="end")


VALID_SIMPLE = ["D1-a", "D1-a-b", "D1-b", "D1-end"]
VALID_SWAP = ["D1-A", "D1-B D2-A", "D1-end D2-B", "D2-end"]


def test_valid_schedule_passes_all_checks() -> None:
    validator = Validator(_simple_map())
    assert validator.check(VALID_SIMPLE) == []
    validator.validate(VALID_SIMPLE)


def test_restricted_forced_landing_is_enforced() -> None:
    lines = ["D1-a", "D1-a-b", "D1-end"]
    violations = Validator(_simple_map()).check(lines)
    assert any("aterrizó" in message for message in violations)
    assert any("promised" in message for message in violations)


def test_zone_capacity_is_rederived_from_output() -> None:
    violations = Validator(_swap_map()).check_zone_capacity(["D1-A D2-A"])
    assert any("zona 'A' sobre capacidad" in message for message in violations)


def test_link_capacity_is_rederived_from_output() -> None:
    violations = Validator(_swap_map()).check_link_capacity_per_turn(["D1-A D2-A"])
    assert any("start-A" in message for message in violations)


def test_swap_is_valid_because_leavers_free_capacity() -> None:
    validator = Validator(_swap_map())
    assert validator.check_leaver_frees_capacity(VALID_SWAP) == []
    validator.validate(VALID_SWAP)


def test_no_leaving_makes_zone_over_capacity() -> None:
    violations = Validator(_swap_map()).check_leaver_frees_capacity(["D1-A", "D2-A"])
    assert violations


def test_d2b_full_period_blocks_back_to_back_use() -> None:
    lines = ["D1-start-r", "D1-r D2-start-r", "D1-end D2-r", "D2-end"]
    strict = Validator(_restricted_shared_map()).check_link_capacity_per_turn(lines)
    relaxed = Validator(
        _restricted_shared_map(), transit_occupies_full_period=False
    ).check_link_capacity_per_turn(lines)
    assert strict
    assert relaxed == []


def test_delivered_drone_is_not_reemitted() -> None:
    violations = Validator(_simple_map()).check_output_coherence(
        [*VALID_SIMPLE, "D1-a"]
    )
    assert any("re-emitido" in message for message in violations)


def test_empty_line_and_turn_prefix_are_rejected() -> None:
    validator = Validator(_simple_map())
    assert any("empty line" in v for v in validator.check_output_coherence([""]))
    assert any("turn prefix" in v for v in validator.check_output_coherence(["turn 1 D1-a"]))


def test_empty_schedule_with_drones_is_a_deadlock() -> None:
    violations = Validator(_simple_map()).check([])
    assert any("deadlock" in message for message in violations)


def test_zero_drones_accepts_empty_schedule() -> None:
    parsed = _simple_map()
    zero = ParsedMap(
        graph=parsed.graph, nb_drones=0, start=parsed.start, end=parsed.end
    )
    Validator(zero).validate([])


def test_validate_raises_schedule_error_with_full_report() -> None:
    with pytest.raises(ScheduleError, match="schedule inválido"):
        Validator(_swap_map()).validate(["D1-A D2-A"])


@pytest.mark.parametrize("map_path", ALL_MAPS, ids=lambda p: str(p.relative_to(MAPS_DIR)))
def test_all_benchmark_maps_pass_the_independent_judge(map_path: Path) -> None:
    """El reporte mínimo de F7.3: 10 casos PASS en el log de pytest."""
    parsed = load_map(map_path)
    plan = Scheduler().plan_validated(
        parsed.graph, parsed.start, parsed.end, parsed.nb_drones
    )
    Validator(parsed).validate(plan.lines)
    assert plan.lines
