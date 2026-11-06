"""Text map → domain graph. Aborts with line + cause on any problem (REQ-PARSE-1)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from flyin.domain.connection import Connection, connection_key
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone, ZoneType
from flyin.parsing.errors import ParseError, ValidationError


# ---------------------------------------------------------------------------
# Parsed map model
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class ParsedMap:
    """Parsed navigable graph and original declarations.

    The fleet is created separately for each simulation run, so it is not
    stored here. Declaration snapshots preserve blocked zones and raw
    connections for independent input validation.
    """

    graph: Graph
    nb_drones: int
    start: str
    end: str
    zone_declarations: tuple[tuple[str, int, str], ...] = ()
    all_zones: Mapping[str, Zone] = field(default_factory=dict)
    all_connections: tuple[tuple[Connection, int], ...] = ()


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

def read_lines(path: Path) -> list[str]:
    """Read the raw map lines using a context manager (REQ-ERR-1, closed handle)."""
    with path.open("r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def _significant_lines(lines: Sequence[str]) -> list[tuple[int, str]]:
    """Return (1-based line number, stripped text) for non-empty, non-comment lines."""
    return [
        (number, raw.strip())
        for number, raw in enumerate(lines, start=1)
        if raw.strip() and not raw.lstrip().startswith("#")
    ]


# ---------------------------------------------------------------------------
# Shared parsing helpers
# ---------------------------------------------------------------------------

def _split_metadata(rest: str, line_no: int) -> tuple[str, str]:
    """Split a line into head and metadata block `[ ... ]`.

    Returns `(head, metadata_without_brackets)`. Raises `ParseError` on malformed
    brackets, trailing text after the block, or nested brackets.
    """
    open_idx = rest.find("[")
    close_idx = rest.rfind("]")
    if open_idx == -1 and close_idx == -1:
        return rest.strip(), ""
    if open_idx == -1 or close_idx == -1:
        raise ParseError("metadato incompleto (falta '[' o ']')", line_no)
    if close_idx < open_idx:
        raise ParseError("']' antes de '['", line_no)
    if rest[close_idx + 1 :].strip():
        raise ParseError("texto despues del bloque de metadatos", line_no)
    metadata = rest[open_idx + 1 : close_idx]
    if "[" in metadata or "]" in metadata:
        raise ParseError("bloque de metadatos anidado", line_no)
    return rest[:open_idx].strip(), metadata


def _parse_metadata(
    metadata: str, line_no: int, allowed: set[str]
) -> list[tuple[str, str]]:
    """Parse a `[key=value ...]` block, validating keys and non-empty values."""
    if not metadata.strip():
        return []
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for token in metadata.split():
        if "=" not in token:
            raise ParseError(f"metadata token {token!r} debe ser key=value", line_no)
        key, value = token.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ParseError(
                f"metadata token {token!r} debe tener key y value no vacíos", line_no
            )
        if key in seen:
            raise ParseError(f"metadata key duplicado {key!r}", line_no)
        if key not in allowed:
            if key in {"zone", "color", "max_drones", "max_link_capacity"}:
                raise ParseError(
                    f"metadata key {key!r} no es válido para esta línea", line_no
                )
            raise ParseError(
                f"key de metadato desconocido {key!r} "
                f"(válidos: {', '.join(sorted(allowed))})",
                line_no,
            )
        seen.add(key)
        pairs.append((key, value))
    return pairs


def _parse_positive_int(value: str, line_no: int, what: str) -> int:
    """Parse a positive integer or abort with a clear cause."""
    try:
        number = int(value)
    except ValueError:
        raise ParseError(f"{what} debe ser entero, got {value!r}", line_no) from None
    if number <= 0:
        raise ValidationError(
            f"{what} debe ser entero positivo, got {number}", line_no
        )
    return number


def _parse_zone_type(value: str, line_no: int) -> ZoneType:
    """Parse a zone type or abort with the list of valid values."""
    try:
        return ZoneType(value)
    except ValueError:
        valid = ", ".join(kind.value for kind in ZoneType)
        raise ParseError(
            f"tipo de zona inválido {value!r} (válidos: {valid})", line_no
        ) from None


# ---------------------------------------------------------------------------
# Declaration parsers
# ---------------------------------------------------------------------------

def _parse_zone_line(
    tag: str, rest: str, line_no: int, declared: dict[str, int]
) -> tuple[Zone, bool, bool]:
    """Parse `start_hub|end_hub|hub: name x y [metadata]`."""
    head, metadata = _split_metadata(rest, line_no)
    parts = head.split()
    if len(parts) != 3:
        raise ParseError(f"{tag} requiere <name> <x> <y>", line_no)
    name, x_str, y_str = parts
    if "-" in name or " " in name:
        raise ParseError(f"nombre de zona {name!r} debe evitar dash y space", line_no)
    try:
        x = int(x_str)
        y = int(y_str)
    except ValueError:
        raise ParseError(f"{tag} coordenadas deben ser enteros", line_no) from None

    is_start = tag == "start_hub"
    is_end = tag == "end_hub"
    zone_type = ZoneType.NORMAL
    cap: int | None = 1
    color: str | None = None

    for key, value in _parse_metadata(
        metadata, line_no, {"zone", "color", "max_drones"}
    ):
        if key == "zone":
            parsed_type = _parse_zone_type(value, line_no)
            if is_start or is_end:
                if parsed_type is ZoneType.BLOCKED:
                    raise ValidationError(
                        f"zone=blocked no permitido en {tag}", line_no
                    )
                # restricted/priority on start/end are ignored: start/end are terminals.
                continue
            zone_type = parsed_type
        elif key == "color":
            color = value
        elif key == "max_drones":
            if is_start or is_end:
                # The subject says max_drones is ignored on start_hub/end_hub.
                continue
            cap = _parse_positive_int(value, line_no, "max_drones")

    if is_start or is_end:
        cap = None

    if name in declared:
        raise ValidationError(
            f"nombre de zona duplicado {name!r} (primera línea {declared[name]})",
            line_no,
        )
    declared[name] = line_no
    zone = Zone(name=name, x=x, y=y, type=zone_type, cap=cap, color=color)
    return zone, is_start, is_end


def _parse_connection_line(
    rest: str, line_no: int, declared: dict[str, int]
) -> tuple[str, str, int]:
    """Parse `connection: name1-name2 [metadata]`; refs must be already declared."""
    head, metadata = _split_metadata(rest, line_no)
    parts = head.split()
    if len(parts) != 1:
        raise ParseError("connection requiere <zone1>-<zone2>", line_no)
    pair = parts[0]
    if pair.count("-") != 1:
        raise ParseError(f"connection {pair!r} debe ser <zone1>-<zone2>", line_no)
    a, b = pair.split("-", 1)
    if not a or not b:
        raise ParseError(
            f"connection {pair!r} debe tener dos nombres no vacíos", line_no
        )
    for name in (a, b):
        if name not in declared:
            raise ValidationError(
                f"connection referencia zona no definida {name!r}", line_no
            )
    cap = 1
    for key, value in _parse_metadata(metadata, line_no, {"max_link_capacity"}):
        if key == "max_link_capacity":
            cap = _parse_positive_int(value, line_no, "max_link_capacity")
    return a, b, cap


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def parse_lines(lines: Sequence[str]) -> ParsedMap:
    """Parse text lines into a `ParsedMap` (pure function: no I/O)."""
    significant = _significant_lines(lines)
    if not significant:
        raise ValidationError("missing nb_drones declaration")

    first_line_no, first_line = significant[0]
    if not first_line.startswith("nb_drones:"):
        raise ValidationError(
            "first non-comment line must be 'nb_drones: <positive_integer>'",
            first_line_no,
        )
    nb_drones = _parse_positive_int(
        first_line.split(":", 1)[1].strip(), first_line_no, "nb_drones"
    )

    declared: dict[str, int] = {}
    zone_declarations: list[tuple[str, int, str]] = []
    zones_by_name: dict[str, Zone] = {}
    connections: list[tuple[Connection, int]] = []
    seen_connections: dict[tuple[str, str], int] = {}
    start: str | None = None
    start_line: int | None = None
    end: str | None = None
    end_line: int | None = None

    for line_no, line in significant[1:]:
        if line.startswith("nb_drones:"):
            raise ValidationError("nb_drones ya declarado", line_no)
        if ":" not in line:
            raise ParseError(f"unknown line type {line!r}", line_no)
        tag, rest = line.split(":", 1)
        tag = tag.strip()
        rest = rest.strip()

        if tag in {"start_hub", "end_hub", "hub"}:
            zone, is_start, is_end = _parse_zone_line(tag, rest, line_no, declared)
            if is_start:
                if start is not None:
                    raise ValidationError(
                        f"duplicate start_hub (first at line {start_line})", line_no
                    )
                start, start_line = zone.name, line_no
            elif is_end:
                if end is not None:
                    raise ValidationError(
                        f"duplicate end_hub (first at line {end_line})", line_no
                    )
                end, end_line = zone.name, line_no
            zones_by_name[zone.name] = zone
            zone_declarations.append((zone.name, line_no, tag))
        elif tag == "connection":
            a, b, cap = _parse_connection_line(rest, line_no, declared)
            key = connection_key(a, b)
            if key in seen_connections:
                raise ValidationError(
                    f"duplicate connection {a!r}-{b!r} "
                    f"(first at line {seen_connections[key]})",
                    line_no,
                )
            seen_connections[key] = line_no
            connections.append((Connection(a=a, b=b, cap=cap), line_no))
        else:
            raise ParseError(f"unknown line type {tag!r}", line_no)

    if start is None:
        raise ValidationError("missing start_hub zone")
    if end is None:
        raise ValidationError("missing end_hub zone")

    # Build the navigable graph: blocked zones are declared (for validation) but pruned.
    graph = Graph()
    for name, zone in zones_by_name.items():
        if zone.type is not ZoneType.BLOCKED:
            graph.add_zone(zone)
    for connection, _line_no in connections:
        if connection.a in graph.zones and connection.b in graph.zones:
            graph.add_connection(connection)

    return ParsedMap(
        graph=graph,
        nb_drones=nb_drones,
        start=start,
        end=end,
        zone_declarations=tuple(zone_declarations),
        all_zones=dict(zones_by_name),
        all_connections=tuple(connections),
    )


def parse_map(path: Path) -> ParsedMap:
    """Read and parse the map at `path` into a navigable `ParsedMap` (F1.2)."""
    return parse_lines(read_lines(path))
