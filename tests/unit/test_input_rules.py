"""Input validation rules (F1.3) — unit tests.

Covers the independent validator that re-derives the domain contract from a
`ParsedMap` without sharing logic with the parser.
"""

from pathlib import Path

import pytest

from flyin.domain.connection import Connection
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone
from flyin.parsing.errors import ValidationError
from flyin.parsing.input_rules import (
    check_no_duplicates,
    check_no_undefined_zones,
    check_positive_capacity,
    check_reachability,
    load_map,
    validate_input,
)
from flyin.parsing.parser import ParsedMap

CANONICAL_MAPS = [
    Path("maps/easy/01_linear_path.txt"),
    Path("maps/easy/02_simple_fork.txt"),
    Path("maps/medium/01_dead_end_trap.txt"),
    Path("maps/hard/01_maze_nightmare.txt"),
]


def _linear_graph() -> Graph:
    """Build `start -- goal` for validator unit tests."""
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0, cap=None))
    graph.add_zone(Zone(name="goal", x=1, y=0, cap=None))
    graph.add_connection(Connection(a="start", b="goal"))
    return graph


def test_load_map_accepts_all_canonical_maps() -> None:
    """F1.3 — every canonical map parses and validates end to end."""
    for path in CANONICAL_MAPS:
        parsed = load_map(path)
        assert parsed.nb_drones > 0
        assert parsed.start in parsed.graph.zones
        assert parsed.end in parsed.graph.zones


def test_check_positive_capacity_accepts_positive() -> None:
    """F1.3 — positive capacities are valid."""
    check_positive_capacity(1, "nb_drones")
    check_positive_capacity(42, "connection start-goal")


@pytest.mark.parametrize("bad", [0, -1, -100])
def test_check_positive_capacity_rejects_non_positive(bad: int) -> None:
    """F1.3 — zero or negative capacities are invalid."""
    with pytest.raises(ValidationError, match="capacity must be > 0"):
        check_positive_capacity(bad, "nb_drones")


def test_check_no_duplicates_accepts_unique_names() -> None:
    """F1.3 — a dict of unique zone names passes the duplicate check."""
    check_no_duplicates({"start": 1, "goal": 2})


def test_check_no_undefined_zones_accepts_valid_graph() -> None:
    """F1.3 — a graph whose connections reference declared zones is valid."""
    check_no_undefined_zones(_linear_graph(), "start", "goal")


def test_check_no_undefined_zones_rejects_missing_start() -> None:
    """F1.3 — a start zone absent from the graph is invalid."""
    with pytest.raises(ValidationError, match="start zone 'ghost' missing"):
        check_no_undefined_zones(_linear_graph(), "ghost", "goal")


def test_check_no_undefined_zones_rejects_missing_end() -> None:
    """F1.3 — an end zone absent from the graph is invalid."""
    with pytest.raises(ValidationError, match="end zone 'ghost' missing"):
        check_no_undefined_zones(_linear_graph(), "start", "ghost")


def test_check_no_undefined_zones_rejects_connection_to_undeclared() -> None:
    """F1.3 — an adjacency entry pointing at a non-declared zone is invalid."""
    graph = _linear_graph()
    # Inject a dangling edge without declaring the target zone.
    graph.adj["start"]["ghost"] = Connection(a="start", b="ghost")
    with pytest.raises(ValidationError, match="undeclared zone 'ghost'"):
        check_no_undefined_zones(graph, "start", "goal")


def test_check_reachability_accepts_connected_graph() -> None:
    """F1.3 — goal reachable from start passes."""
    check_reachability(_linear_graph(), "start", "goal")


def test_check_reachability_rejects_disconnected_graph() -> None:
    """F1.3 — goal unreachable from start is invalid."""
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0, cap=None))
    graph.add_zone(Zone(name="island", x=5, y=5, cap=None))
    with pytest.raises(ValidationError, match="not reachable"):
        check_reachability(graph, "start", "island")


def test_validate_input_rejects_zero_drones() -> None:
    """F1.3 — a ParsedMap with nb_drones == 0 is rejected."""
    parsed = ParsedMap(graph=_linear_graph(), nb_drones=0, start="start", end="goal")
    with pytest.raises(ValidationError, match="nb_drones capacity must be > 0"):
        validate_input(parsed)


def test_validate_input_rejects_non_positive_link_capacity() -> None:
    """F1.3 — a connection with cap <= 0 is rejected."""
    graph = Graph()
    graph.add_zone(Zone(name="start", x=0, y=0, cap=None))
    graph.add_zone(Zone(name="goal", x=1, y=0, cap=None))
    graph.add_connection(Connection(a="start", b="goal", cap=0))
    parsed = ParsedMap(graph=graph, nb_drones=1, start="start", end="goal")
    with pytest.raises(ValidationError, match="capacity must be > 0"):
        validate_input(parsed)


def test_validate_input_accepts_valid_parsed_map() -> None:
    """F1.3 — a fully valid ParsedMap passes every rule."""
    parsed = ParsedMap(graph=_linear_graph(), nb_drones=3, start="start", end="goal")
    validate_input(parsed)


def test_load_map_missing_file_raises() -> None:
    """REQ-ERR-1 — a missing map file surfaces FileNotFoundError, not a crash."""
    with pytest.raises(FileNotFoundError):
        load_map(Path("/tmp/does_not_exist_flyin_map.txt"))
