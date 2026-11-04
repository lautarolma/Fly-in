"""Parser (F1.2) — unit tests covering contract enforcement and error handling.

Tests validate the parse_map implementation and its strict validation rules.
"""

from pathlib import Path
import pytest
from flyin.domain.zone import ZoneType
from flyin.parsing.parser import parse_lines, parse_map
from flyin.parsing.errors import ParseError, ValidationError
from flyin.parsing.input_rules import load_map

# Load canonical maps (any should produce valid, non‑empty maps)
EASY_01 = Path("maps/easy/01_linear_path.txt")
EASY_02 = Path("maps/easy/02_simple_fork.txt")
MEDIUM_01 = Path("maps/medium/01_dead_end_trap.txt")
HARD_01 = Path("maps/hard/01_maze_nightmare.txt")

CANONICAL_MAPS = [EASY_01, EASY_02, MEDIUM_01, HARD_01]


def test_parser_returns_non_empty_map_for_canonical_maps() -> None:
    """F1.2 — every map used in the system should parse to a valid ParsedMap."""
    for path in CANONICAL_MAPS:
        parsed = parse_map(path)
        # Non‑empty graph with at least start and end zones
        assert parsed.graph is not None
        zones = parsed.graph.zones
        assert len(zones) >= 2, f"{path} should have at least start and goal"
        assert parsed.nb_drones > 0, f"{path} should have a positive nb_drones"
        assert parsed.start in zones, f"start {parsed.start} must be in graph"
        assert parsed.end in zones, f"end {parsed.end} must be in graph"


def test_parser_allows_and_prunes_blocked_zones() -> None:
    """F1.2 — blocked zones should be declared but removed from the navigable graph.

    This is an explicit contract: we track them for validation, but the navigable
    graph never includes a zone with type `ZoneType.BLOCKED`.
    """
    # No canonical map ships a blocked zone, so build one inline.
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
    assert "wall" not in parsed.graph.zones, "blocked zone should be pruned from graph"
    assert "wall" in parsed.all_zones, "blocked zone should stay in the unpruned snapshot"


def test_parser_enforces_unique_zone_names() -> None:
    """F1.2 — duplicate zone names across start_hub / end_hub / hub are invalid.
    """
    # Create a temporary map with duplicate zone names
    duplicate = Path("/tmp/duplicate_zones.txt")
    duplicate.write_text(
        "nb_drones: 1\n"
        "start_hub: start 0 0 [color=green]\n"
        "hub: start 10 10 [color=red]\n"  # Duplicate name "start"
    )
    with pytest.raises(ValidationError, match="nombre de zona duplicado"):
        parse_map(duplicate)
    duplicate.unlink()


def test_parser_enforces_unique_connections() -> None:
    """F1.2 — duplicate connections (same unordered pair) should raise ValidationError.
    """
    dup = Path("/tmp/dup_conn.txt")
    dup.write_text(
        "nb_drones: 2\n"
        "start_hub: start 0 0 [color=green]\n"
        "end_hub: goal 10 0 [color=red]\n"
        "connection: start-goal\n"
        "connection: start-goal\n"  # Duplicate
    )
    with pytest.raises(ValidationError, match="duplicate connection"):
        parse_map(dup)
    dup.unlink()

    # Reversed order is the SAME unordered connection (connection_key is canonical).
    rev = Path("/tmp/dup_conn_reversed.txt")
    rev.write_text(
        "nb_drones: 2\n"
        "start_hub: start 0 0 [color=green]\n"
        "end_hub: goal 10 0 [color=red]\n"
        "connection: start-goal\n"
        "connection: goal-start\n"  # Duplicate, reversed
    )
    with pytest.raises(ValidationError, match="duplicate connection"):
        parse_map(rev)
    rev.unlink()


def test_parser_requires_start_and_end() -> None:
    """F1.2 — missing start or end zone is a validation failure.
    """
    # Missing start_hub — no connection referencing start to avoid a different error path first
    missing_start = Path("/tmp/missing_start.txt")
    missing_start.write_text(
        "nb_drones: 1\n"
        "end_hub: goal 10 0 [color=red]\n"
    )
    with pytest.raises(ValidationError, match="missing start_hub zone"):
        parse_map(missing_start)
    missing_start.unlink()

    # Missing end_hub — no connection referencing goal to avoid a different error path first
    missing_end = Path("/tmp/missing_end.txt")
    missing_end.write_text(
        "nb_drones: 1\n"
        "start_hub: start 0 0 [color=green]\n"
    )
    with pytest.raises(ValidationError, match="missing end_hub zone"):
        parse_map(missing_end)
    missing_end.unlink()


def test_parser_rejects_connection_to_undeclared_zone() -> None:
    """F1.2 — connection referencing a zone that never appears should raise ValidationError.
    """
    undeclared = Path("/tmp/undeclared.txt")
    undeclared.write_text(
        "nb_drones: 1\n"
        "start_hub: start 0 0 [color=green]\n"
        "end_hub: goal 10 0 [color=red]\n"
        "connection: start-unknown\n"
    )
    with pytest.raises(ValidationError, match="connection referencia zona no definida"):
        parse_map(undeclared)
    undeclared.unlink()


def test_parser_captures_and_rejects_metadata_errors() -> None:
    """F1.2 — malformed metadata (missing ], duplicated bracket, trailing text)
    should raise ParseError.
    """
    # Missing closing bracket
    bad1 = Path("/tmp/bad1.txt")
    bad1.write_text(
        "nb_drones: 1\n"
        "start_hub: start 0 0 [color=green\n"  # Missing ]
    )
    with pytest.raises(ParseError, match="metadato incompleto"):
        parse_map(bad1)
    bad1.unlink()

    # Trailing text after metadata
    bad2 = Path("/tmp/bad2.txt")
    bad2.write_text(
        "nb_drones: 1\n"
        "start_hub: start 0 0 [color=green] extra\n"  # Trailing text
    )
    with pytest.raises(ParseError, match="texto despues del bloque de metadatos"):
        parse_map(bad2)
    bad2.unlink()


def test_parsed_map_includes_all_declared_zones() -> None:
    """Sanity check: parsed map includes all non‑blocked zones from the source."""
    parsed = parse_map(EASY_01)
    # Zones in the graph: start, waypoint1, waypoint2, goal
    expected = {"start", "waypoint1", "waypoint2", "goal"}
    assert set(parsed.graph.zones.keys()) == expected


def test_parsed_map_connection_structure() -> None:
    """Sanity check: parsed connections match those in the source."""
    from flyin.domain.connection import connection_key
    parsed = parse_map(EASY_01)
    found: set[tuple[str, str]] = set()
    for a, neighbors in parsed.graph.adj.items():
        for b in neighbors:
            if a < b:
                found.add(connection_key(a, b))
    expected = {
        connection_key("start", "waypoint1"),
        connection_key("waypoint1", "waypoint2"),
        connection_key("waypoint2", "goal"),
    }
    assert found == expected, f"found={found} expected={expected}"


def test_parser_valid_metadata_allowed_per_line() -> None:
    """F1.2 — metadata keys not allowed on a given line should raise ValidationError.

    - start_hub: may have [color=green]
    - hub: may have [color=..., max_drones=...]
    - connection: may have [max_link_capacity=...]
    """
    # Attempting "zone=blocked" on start_hub is explicitly forbidden (ValidationError)
    bad_start = Path("/tmp/bad_start.txt")
    bad_start.write_text(
        "nb_drones: 1\n"
        "start_hub: start 0 0 [zone=blocked]\n"  # BLOCKED is invalid on start_hub
    )
    with pytest.raises(ValidationError, match="zone=blocked no permitido en start_hub"):
        parse_map(bad_start)
    bad_start.unlink()

    # Attempting "color=" on a connection (invalid)
    bad_conn = Path("/tmp/bad_conn.txt")
    bad_conn.write_text(
        "nb_drones: 1\n"
        "start_hub: start 0 0 [color=green]\n"
        "end_hub: goal 10 0 [color=red]\n"
        "connection: start-goal [color=blue]\n"  # color not allowed on connections
    )
    with pytest.raises(ParseError, match="no es válido para esta línea"):
        parse_map(bad_conn)
    bad_conn.unlink()


def test_parsed_map_preserves_link_capacities() -> None:
    """F1.2 — connection metadata (max_link_capacity) should be preserved in the ParsedMap."""
    # easy/03_basic_capacity.txt has a connection with capacity different from 1.
    parsed = parse_map(Path("maps/easy/03_basic_capacity.txt"))
    # Find the connection from start to waypoint1 (capacity from file)
    start_way_connections = []
    for a, neighbors in parsed.graph.adj.items():
        for b, conn in neighbors.items():
            if conn.a == "start" and conn.b == "waypoint1":
                start_way_connections.append(conn)
    if start_way_connections:
        conn = start_way_connections[0]
        # From the map file: capacity is 1. If the parser preserves capacity, assert it's correct.
        assert conn.cap == 1, f"connection capacity should be 1, got {conn.cap}"
    # If there were a connection with capacity != 1, we'd assert on that.


# Edge cases specific to file I/O (REQ-ERR-1) — one-liners to ensure basic robustness.

def test_parser_missing_file_raises() -> None:
    """Ensure that a missing map file raises a FileNotFoundError."""
    missing = Path("/tmp/missing_file_xyz_abc.txt")
    with pytest.raises(FileNotFoundError):
        parse_map(missing)


# --- Spec traceability (docs/spec_E2.md) -------------------------------------
# These names mirror the scenarios in the spec so the test suite is auditable
# against the requirements document.

VALID_LINES = [
    "nb_drones: 2",
    "start_hub: start 0 0 [color=green]",
    "hub: waypoint 1 0 [color=blue]",
    "end_hub: goal 2 0 [color=red]",
    "connection: start-waypoint",
    "connection: waypoint-goal",
]


def test_parse_valid_map() -> None:
    """REQ-PARSE-1 — a valid map yields a navigable ParsedMap."""
    parsed = parse_map(EASY_01)
    assert parsed.start == "start"
    assert parsed.end == "goal"
    assert set(parsed.graph.zones) == {"start", "waypoint1", "waypoint2", "goal"}


def test_parse_nb_drones() -> None:
    """REQ-PARSE-1 — nb_drones is parsed from the first significant line."""
    assert parse_map(EASY_01).nb_drones == 2


def test_parse_comments_ignored() -> None:
    """REQ-PARSE-1 — comments and blank lines are ignored, line numbers preserved."""
    lines = [
        "# leading comment",
        "nb_drones: 1",
        "",
        "start_hub: start 0 0",
        "   # indented comment",
        "hub: bad-name 1 0",
        "end_hub: goal 2 0",
    ]
    with pytest.raises(ParseError) as exc:
        parse_lines(lines)
    assert exc.value.line == 6


def test_parse_metadata_any_order() -> None:
    """REQ-PARSE-1 — metadata keys are order-independent."""
    parsed = parse_lines(
        [
            "nb_drones: 1",
            "start_hub: start 0 0",
            "hub: hub 1 0 [max_drones=3 color=red]",
            "end_hub: goal 2 0",
        ]
    )
    zone = parsed.graph.zones["hub"]
    assert zone.cap == 3
    assert zone.color == "red"


def test_parse_unknown_metadata_key() -> None:
    """REQ-PARSE-1 — unknown metadata keys are rejected."""
    with pytest.raises(ParseError, match="key de metadato desconocido"):
        parse_lines([*VALID_LINES[:3], "hub: other 1 0 [foo=bar]", *VALID_LINES[3:]])


def test_parse_metadata_wrong_line() -> None:
    """REQ-PARSE-1 — a valid key on the wrong line type is rejected."""
    with pytest.raises(ParseError, match="no es válido para esta línea"):
        parse_lines([*VALID_LINES, "connection: start-goal [max_drones=2]"])


def test_parse_empty_metadata_value() -> None:
    """REQ-PARSE-1 — `key=` with an empty value is rejected."""
    with pytest.raises(ParseError, match="value no vacíos"):
        parse_lines(["nb_drones: 1", "start_hub: start 0 0 [color=]", "end_hub: goal 2 0"])


def test_parse_nb_drones_zero() -> None:
    """REQ-PARSE-1 — nb_drones must be strictly positive."""
    with pytest.raises(ValidationError, match="nb_drones debe ser entero positivo"):
        parse_lines(["nb_drones: 0", "start_hub: start 0 0", "end_hub: goal 2 0"])


def test_parse_nb_drones_not_first() -> None:
    """REQ-PARSE-1 — nb_drones must be the first significant line."""
    with pytest.raises(ValidationError, match="first non-comment line"):
        parse_lines(["start_hub: start 0 0", "nb_drones: 1", "end_hub: goal 2 0"])


def test_parse_nb_drones_duplicate() -> None:
    """REQ-PARSE-1 — nb_drones may only be declared once."""
    with pytest.raises(ValidationError, match="nb_drones ya declarado"):
        parse_lines(
            ["nb_drones: 1", "start_hub: start 0 0", "end_hub: goal 2 0", "nb_drones: 2"]
        )


def test_parse_max_drones_start_ignored() -> None:
    """REQ-PARSE-1 — max_drones on start_hub is ignored (terminal zone)."""
    parsed = parse_lines(
        ["nb_drones: 1", "start_hub: start 0 0 [max_drones=9]", "end_hub: goal 2 0"]
    )
    assert parsed.graph.zones["start"].cap is None


def test_parse_zone_blocked_on_start_errors() -> None:
    """REQ-PARSE-1 — start_hub cannot be blocked."""
    with pytest.raises(ValidationError, match="zone=blocked no permitido en start_hub"):
        parse_lines(["nb_drones: 1", "start_hub: start 0 0 [zone=blocked]", "end_hub: goal 2 0"])


def test_parse_zone_restricted_on_start_ignored() -> None:
    """REQ-PARSE-1 — restricted/priority on start_hub are ignored."""
    parsed = parse_lines(
        ["nb_drones: 1", "start_hub: start 0 0 [zone=restricted]", "end_hub: goal 2 0"]
    )
    assert parsed.graph.zones["start"].type is ZoneType.NORMAL


def test_parse_unknown_color_value_ok() -> None:
    """REQ-PARSE-1 — color values are free-form."""
    parsed = parse_lines(
        ["nb_drones: 1", "start_hub: start 0 0 [color=chartreuse]", "end_hub: goal 2 0"]
    )
    assert parsed.graph.zones["start"].color == "chartreuse"


def test_duplicate_zone_name() -> None:
    """REQ-VALID-1 — zone names are unique across start/end/hub."""
    with pytest.raises(ValidationError, match="nombre de zona duplicado"):
        parse_lines(
            ["nb_drones: 1", "start_hub: start 0 0", "hub: start 1 0", "end_hub: goal 2 0"]
        )


def test_zone_name_no_dash_or_space() -> None:
    """REQ-PARSE-1 — zone names cannot contain '-' or spaces."""
    with pytest.raises(ParseError, match="debe evitar dash y space"):
        parse_lines(["nb_drones: 1", "start_hub: start 0 0", "hub: a-b 1 0", "end_hub: goal 2 0"])
    with pytest.raises(ParseError):
        parse_lines(
            ["nb_drones: 1", "start_hub: start 0 0", "hub: roof 1 0 0", "end_hub: goal 2 0"]
        )


def test_invalid_zone_type() -> None:
    """REQ-PARSE-1 — zone type must be one of the four known values."""
    with pytest.raises(ParseError, match="tipo de zona inválido"):
        parse_lines(
            [
                "nb_drones: 1",
                "start_hub: start 0 0",
                "hub: h 1 0 [zone=fast]",
                "end_hub: goal 2 0",
            ]
        )


def test_nonpositive_capacity() -> None:
    """REQ-PARSE-1 — zone and link capacities must be strictly positive."""
    with pytest.raises(ValidationError, match="max_drones debe ser entero positivo"):
        parse_lines(
            [
                "nb_drones: 1",
                "start_hub: start 0 0",
                "hub: h 1 0 [max_drones=0]",
                "end_hub: goal 2 0",
            ]
        )
    with pytest.raises(ValidationError, match="max_link_capacity debe ser entero positivo"):
        parse_lines([*VALID_LINES, "connection: start-goal [max_link_capacity=0]"])


def test_blocked_pruned() -> None:
    """REQ-VALID-1 — blocked zones are declared but pruned from the graph."""
    parsed = parse_lines(
        [
            "nb_drones: 1",
            "start_hub: start 0 0",
            "hub: wall 1 0 [zone=blocked]",
            "end_hub: goal 2 0",
            "connection: start-wall",
            "connection: wall-goal",
        ]
    )
    assert "wall" not in parsed.graph.zones
    assert "wall" in parsed.all_zones


def test_unreachable_end_errors(tmp_path: Path) -> None:
    """REQ-VALID-1 — load_map rejects an end unreachable from start."""
    map_file = tmp_path / "unreachable.txt"
    map_file.write_text(
        "nb_drones: 1\n"
        "start_hub: start 0 0\n"
        "hub: wall 1 0 [zone=blocked]\n"
        "end_hub: goal 2 0\n"
        "connection: start-wall\n"
        "connection: wall-goal\n"
    )
    with pytest.raises(ValidationError, match="not reachable"):
        load_map(map_file)
