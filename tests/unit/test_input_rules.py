"""Input validation rules (F1.3) — unit tests.

Covers the independent validator that re-derives the domain contract from the
unpruned snapshot carried by `ParsedMap` without sharing logic with the parser.
"""

from pathlib import Path

import pytest

from flyin.domain.connection import Connection
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone, ZoneType
from flyin.parsing.errors import ValidationError
from flyin.parsing.input_rules import (
    check_blocked_pruned,
    check_connection_refs,
    check_no_duplicate_connections,
    check_positive_capacities,
    check_positive_capacity,
    check_reachability,
    check_single_start_end,
    check_unique_zone_names,
    check_zone_name_chars,
    check_zone_types,
    load_map,
    validate_input,
)
from flyin.parsing.parser import ParsedMap, parse_lines

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


def _linear_parsed() -> ParsedMap:
    """Hand-built ParsedMap with a minimal, coherent snapshot."""
    return ParsedMap(
        graph=_linear_graph(),
        nb_drones=1,
        start="start",
        end="goal",
        zone_declarations=(("start", 1, "start_hub"), ("goal", 2, "end_hub")),
        all_zones={
            "start": Zone(name="start", x=0, y=0, cap=None),
            "goal": Zone(name="goal", x=1, y=0, cap=None),
        },
        all_connections=((Connection(a="start", b="goal"), 3),),
    )


def test_load_map_accepts_all_canonical_maps() -> None:
    """F1.3 — every canonical map parses and validates end to end."""
    for path in CANONICAL_MAPS:
        parsed = load_map(path)
        assert parsed.nb_drones > 0
        assert parsed.start in parsed.graph.zones
        assert parsed.end in parsed.graph.zones


def test_parsed_map_exposes_unpruned_snapshot() -> None:
    """REQ-VALID-1 — the snapshot keeps blocked zones and their connections."""
    parsed = parse_lines(
        [
            "nb_drones: 1",
            "start_hub: start 0 0 [color=green]",
            "hub: wall 1 0 [zone=blocked]",
            "end_hub: goal 2 0 [color=red]",
            "connection: start-wall",
            "connection: wall-goal",
        ]
    )
    assert ("wall", 3, "hub") in parsed.zone_declarations
    assert "wall" in parsed.all_zones
    assert parsed.all_zones["wall"].type is ZoneType.BLOCKED
    assert len(parsed.all_connections) == 2
    assert "wall" not in parsed.graph.zones


def test_check_positive_capacity_accepts_positive() -> None:
    """F1.3 — positive capacities are valid."""
    check_positive_capacity(1, "nb_drones")
    check_positive_capacity(42, "connection start-goal")


@pytest.mark.parametrize("bad", [0, -1, -100])
def test_check_positive_capacity_rejects_non_positive(bad: int) -> None:
    """F1.3 — zero or negative capacities are invalid."""
    with pytest.raises(ValidationError, match="capacity must be > 0"):
        check_positive_capacity(bad, "nb_drones")


def test_check_positive_capacities_accepts_valid_map() -> None:
    """F1.3 — a coherent map passes the capacity sweep."""
    check_positive_capacities(_linear_parsed())


def test_check_positive_capacities_rejects_zero_zone_capacity() -> None:
    """F1.3 — a zone with cap == 0 is rejected."""
    parsed = ParsedMap(
        graph=_linear_graph(),
        nb_drones=1,
        start="start",
        end="goal",
        zone_declarations=(("start", 1, "start_hub"), ("goal", 2, "end_hub")),
        all_zones={
            "start": Zone(name="start", x=0, y=0, cap=None),
            "goal": Zone(name="goal", x=1, y=0, cap=0),
        },
    )
    with pytest.raises(ValidationError, match="zone 'goal' capacity must be > 0"):
        check_positive_capacities(parsed)


def test_check_positive_capacities_rejects_zero_link_capacity() -> None:
    """F1.3 — a connection with cap == 0 is rejected."""
    parsed = ParsedMap(
        graph=_linear_graph(),
        nb_drones=1,
        start="start",
        end="goal",
        zone_declarations=(("start", 1, "start_hub"), ("goal", 2, "end_hub")),
        all_zones={
            "start": Zone(name="start", x=0, y=0, cap=None),
            "goal": Zone(name="goal", x=1, y=0, cap=None),
        },
        all_connections=((Connection(a="start", b="goal", cap=0), 3),),
    )
    with pytest.raises(ValidationError, match="capacity must be > 0"):
        check_positive_capacities(parsed)


def test_check_single_start_end_accepts_one_of_each() -> None:
    """F1.3 — exactly one start_hub and one end_hub is valid."""
    check_single_start_end(_linear_parsed())


def test_check_single_start_end_rejects_missing_end() -> None:
    """F1.3 — a map without end_hub is rejected."""
    parsed = ParsedMap(
        graph=_linear_graph(),
        nb_drones=1,
        start="start",
        end="goal",
        zone_declarations=(("start", 1, "start_hub"),),
    )
    with pytest.raises(ValidationError, match="expected exactly one end_hub, got 0"):
        check_single_start_end(parsed)


def test_check_unique_zone_names_accepts_unique_names() -> None:
    """F1.3 — unique declared names pass."""
    check_unique_zone_names(_linear_parsed())


def test_check_unique_zone_names_rejects_duplicate() -> None:
    """F1.3 — a repeated zone name is rejected."""
    parsed = ParsedMap(
        graph=_linear_graph(),
        nb_drones=1,
        start="start",
        end="goal",
        zone_declarations=(
            ("start", 1, "start_hub"),
            ("goal", 2, "end_hub"),
            ("start", 3, "hub"),
        ),
    )
    with pytest.raises(ValidationError, match="duplicate zone name 'start'"):
        check_unique_zone_names(parsed)


def test_check_zone_name_chars_rejects_dash() -> None:
    """F1.3 — a zone name containing '-' is rejected."""
    parsed = ParsedMap(
        graph=_linear_graph(),
        nb_drones=1,
        start="start",
        end="goal",
        zone_declarations=(
            ("start", 1, "start_hub"),
            ("go-al", 2, "end_hub"),
        ),
    )
    with pytest.raises(ValidationError, match="must not contain '-' or space"):
        check_zone_name_chars(parsed)


def test_check_zone_types_accepts_valid_types() -> None:
    """F1.3 — every declared zone carries a valid ZoneType."""
    check_zone_types(_linear_parsed())


def test_check_connection_refs_uses_unpruned_declared_set() -> None:
    """REQ-VALID-1 — endpoints may reference a declared `blocked` zone."""
    parsed = parse_lines(
        [
            "nb_drones: 1",
            "start_hub: start 0 0 [color=green]",
            "hub: wall 1 0 [zone=blocked]",
            "end_hub: goal 2 0 [color=red]",
            "connection: start-wall",
            "connection: wall-goal",
        ]
    )
    # `wall` is not in graph.zones but IS declared, so refs are valid.
    check_connection_refs(parsed)


def test_check_connection_refs_rejects_undeclared_endpoint() -> None:
    """F1.3 — an endpoint that was never declared is rejected."""
    parsed = ParsedMap(
        graph=_linear_graph(),
        nb_drones=1,
        start="start",
        end="goal",
        zone_declarations=(("start", 1, "start_hub"), ("goal", 2, "end_hub")),
        all_connections=((Connection(a="start", b="ghost"), 3),),
    )
    with pytest.raises(ValidationError, match="undeclared zone 'ghost'"):
        check_connection_refs(parsed)


def test_check_no_duplicate_connections_accepts_unique_pairs() -> None:
    """F1.3 — distinct unordered pairs pass."""
    check_no_duplicate_connections(_linear_parsed())


def test_check_no_duplicate_connections_rejects_reversed_duplicate() -> None:
    """F1.3 — `start-goal` and `goal-start` are the same unordered pair."""
    parsed = ParsedMap(
        graph=_linear_graph(),
        nb_drones=1,
        start="start",
        end="goal",
        zone_declarations=(("start", 1, "start_hub"), ("goal", 2, "end_hub")),
        all_connections=(
            (Connection(a="start", b="goal"), 3),
            (Connection(a="goal", b="start"), 4),
        ),
    )
    with pytest.raises(ValidationError, match="duplicate connection"):
        check_no_duplicate_connections(parsed)


def test_check_blocked_pruned_accepts_pruned_blocked_zone() -> None:
    """F1.3 — blocked zones and incident connections are pruned from the graph."""
    parsed = parse_lines(
        [
            "nb_drones: 1",
            "start_hub: start 0 0 [color=green]",
            "hub: wall 1 0 [zone=blocked]",
            "end_hub: goal 2 0 [color=red]",
            "connection: start-wall",
            "connection: wall-goal",
        ]
    )
    check_blocked_pruned(parsed)


def test_check_blocked_pruned_rejects_leaked_blocked_zone() -> None:
    """F1.3 — a blocked zone present in the navigable graph is rejected."""
    graph = _linear_graph()
    graph.add_zone(Zone(name="wall", x=2, y=0, type=ZoneType.BLOCKED))
    parsed = ParsedMap(
        graph=graph,
        nb_drones=1,
        start="start",
        end="goal",
        zone_declarations=(
            ("start", 1, "start_hub"),
            ("goal", 2, "end_hub"),
            ("wall", 3, "hub"),
        ),
        all_zones={"wall": Zone(name="wall", x=2, y=0, type=ZoneType.BLOCKED)},
    )
    with pytest.raises(ValidationError, match="blocked zone 'wall' must be pruned"):
        check_blocked_pruned(parsed)


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
    validate_input(_linear_parsed())


def test_load_map_missing_file_raises() -> None:
    """REQ-ERR-1 — a missing map file surfaces FileNotFoundError, not a crash."""
    with pytest.raises(FileNotFoundError):
        load_map(Path("/tmp/does_not_exist_flyin_map.txt"))
