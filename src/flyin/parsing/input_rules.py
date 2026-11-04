"""Input validation rules (F1.3) — independent re-derivation of the domain contract.

This module shares NO logic with the parser. It re-derives every rule from the
**unpruned snapshot** carried by `ParsedMap` (`zone_declarations`, `all_zones`,
`all_connections`) plus the navigable `graph`. A parser bug that lets a bad value
through is caught here.

Why the snapshot? The navigable graph prunes `blocked` zones and every connection
incident to them, so rules such as "connection endpoints must reference a declared
zone" or "no duplicate connection lines" cannot be re-derived from the graph alone
(REQ-VALID-1). The snapshot preserves exactly what the input declared.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from flyin.domain.connection import connection_key
from flyin.domain.graph import Graph
from flyin.domain.zone import ZoneType
from flyin.parsing.errors import ValidationError
from flyin.parsing.parser import ParsedMap, parse_map


def check_positive_capacity(cap: int, where: str, line: int | None = None) -> None:
    """Every capacity value must be a strictly positive integer."""
    if cap <= 0:
        raise ValidationError(f"{where} capacity must be > 0, got {cap}", line)


def check_single_start_end(parsed: ParsedMap) -> None:
    """The map must declare exactly one `start_hub` and exactly one `end_hub`."""
    starts = [line for _name, line, tag in parsed.zone_declarations if tag == "start_hub"]
    ends = [line for _name, line, tag in parsed.zone_declarations if tag == "end_hub"]
    if len(starts) != 1:
        line = starts[1] if len(starts) > 1 else None
        raise ValidationError(f"expected exactly one start_hub, got {len(starts)}", line)
    if len(ends) != 1:
        line = ends[1] if len(ends) > 1 else None
        raise ValidationError(f"expected exactly one end_hub, got {len(ends)}", line)
    if parsed.start == parsed.end:
        raise ValidationError("start_hub and end_hub must be different zones")


def check_unique_zone_names(parsed: ParsedMap) -> None:
    """No zone name may be declared more than once (start/end/hub share the namespace)."""
    seen: dict[str, int] = {}
    for name, line, _tag in parsed.zone_declarations:
        if name in seen:
            raise ValidationError(
                f"duplicate zone name {name!r} (first at line {seen[name]})", line
            )
        seen[name] = line


def check_zone_name_chars(parsed: ParsedMap) -> None:
    """Zone names must not contain `-` (connection separator) or spaces."""
    for name, line, _tag in parsed.zone_declarations:
        if "-" in name or " " in name:
            raise ValidationError(
                f"zone name {name!r} must not contain '-' or space", line
            )


def check_zone_types(parsed: ParsedMap) -> None:
    """Every declared zone must carry a valid `ZoneType`."""
    for name, line, _tag in parsed.zone_declarations:
        zone = parsed.all_zones.get(name)
        if zone is None:
            raise ValidationError(f"zone {name!r} declared but missing from snapshot", line)
        if not isinstance(zone.type, ZoneType):
            raise ValidationError(f"zone {name!r} has invalid type {zone.type!r}", line)


def check_positive_capacities(parsed: ParsedMap) -> None:
    """`nb_drones`, every zone capacity and every connection capacity must be > 0."""
    check_positive_capacity(parsed.nb_drones, "nb_drones")
    if not parsed.zone_declarations:
        # Hand-built ParsedMap (unit tests): fall back to graph-derived data.
        for a, neighbors in parsed.graph.adj.items():
            for b, conn in neighbors.items():
                check_positive_capacity(conn.cap, f"connection {a}-{b}")
        return
    for name, line, _tag in parsed.zone_declarations:
        zone = parsed.all_zones.get(name)
        if zone is not None and zone.cap is not None:
            check_positive_capacity(zone.cap, f"zone {name!r}", line)
    for connection, line in parsed.all_connections:
        check_positive_capacity(
            connection.cap, f"connection {connection.a}-{connection.b}", line
        )


def check_connection_refs(parsed: ParsedMap) -> None:
    """Every connection endpoint must reference a declared zone, including `blocked`.

    Comparison uses the **unpruned** declared set, never `graph.zones` (REQ-VALID-1).
    """
    declared = {name for name, _line, _tag in parsed.zone_declarations}
    for connection, line in parsed.all_connections:
        for endpoint in (connection.a, connection.b):
            if endpoint not in declared:
                raise ValidationError(
                    f"connection references undeclared zone {endpoint!r}", line
                )
    for endpoint in (parsed.start, parsed.end):
        if endpoint not in declared:
            raise ValidationError(f"{endpoint!r} is not a declared zone")


def check_no_duplicate_connections(parsed: ParsedMap) -> None:
    """No unordered zone pair may be connected more than once."""
    seen: dict[tuple[str, str], int] = {}
    for connection, line in parsed.all_connections:
        key = connection_key(connection.a, connection.b)
        if key in seen:
            raise ValidationError(
                f"duplicate connection {connection.a!r}-{connection.b!r} "
                f"(first at line {seen[key]})",
                line,
            )
        seen[key] = line


def check_blocked_pruned(parsed: ParsedMap) -> None:
    """`blocked` zones and every connection incident to them must be pruned."""
    blocked = {
        name
        for name, _line, _tag in parsed.zone_declarations
        if (zone := parsed.all_zones.get(name)) is not None
        and zone.type is ZoneType.BLOCKED
    }
    for name in blocked:
        if name in parsed.graph.zones:
            raise ValidationError(
                f"blocked zone {name!r} must be pruned from the navigable graph"
            )
    for a, neighbors in parsed.graph.adj.items():
        if a in blocked:
            raise ValidationError(
                f"navigable graph must not contain blocked zone {a!r}"
            )
        for b in neighbors:
            if b in blocked:
                raise ValidationError(
                    f"connection {a!r}-{b!r} incident to blocked zone must be pruned"
                )


def check_reachability(graph: Graph, start: str, end: str) -> None:
    """The end zone must be reachable from the start zone (unweighted BFS)."""
    if start not in graph.zones or end not in graph.zones:
        raise ValidationError("start or end zone missing from navigable graph")
    visited: set[str] = {start}
    queue: deque[str] = deque([start])
    while queue:
        node = queue.popleft()
        if node == end:
            return
        for neighbor in graph.adj.get(node, {}):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    raise ValidationError(f"end zone {end!r} is not reachable from start {start!r}")


def validate_input(parsed: ParsedMap) -> None:
    """Run every input validation rule against a parsed map (F1.3).

    Order matters: capacities first (cheapest, most local), then the structural
    snapshot rules, then reachability (needs a coherent graph).
    """
    check_positive_capacities(parsed)
    if parsed.zone_declarations:
        check_single_start_end(parsed)
        check_unique_zone_names(parsed)
        check_zone_name_chars(parsed)
        check_zone_types(parsed)
        check_connection_refs(parsed)
        check_no_duplicate_connections(parsed)
        check_blocked_pruned(parsed)
    else:
        # Hand-built ParsedMap (unit tests): only graph-derived data is available.
        for endpoint in (parsed.start, parsed.end):
            if endpoint not in parsed.graph.zones:
                raise ValidationError(f"zone {endpoint!r} missing from navigable graph")
    check_reachability(parsed.graph, parsed.start, parsed.end)


def load_map(path: Path) -> ParsedMap:
    """Parse and validate a map file (F1.2 + F1.3).

    Combines `parse_map` (syntax) with `validate_input` (semantics) and returns a
    fully validated `ParsedMap`.
    """
    parsed = parse_map(path)
    validate_input(parsed)
    return parsed
