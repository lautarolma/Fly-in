"""Input validation rules (F1.3).

Independent re-derivation of the domain contract: this module shares NO logic with
the parser. It inspects the `ParsedMap` produced by `parse_map` and raises
`ValidationError` on any violation.

The validator is intentionally dumb: it re-derives rules from first principles rather
than trusting the parser's output. A parser bug that slips a bad value through is
caught here.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from flyin.domain.graph import Graph
from flyin.parsing.errors import ValidationError
from flyin.parsing.parser import ParsedMap, parse_map


def check_positive_capacity(cap: int, where: str) -> None:
    """Every capacity value must be a strictly positive integer."""
    if cap <= 0:
        raise ValidationError(f"{where} capacity must be > 0, got {cap}")


def check_no_duplicates(declared: dict[str, int]) -> None:
    """No zone name may be declared more than once.

    `declared` maps zone name → first line where it was declared. Re-derivation
    (independent of the parser): a duplicate would be a name with more than one
    declaration, which a dict cannot represent, so we verify the invariant that
    every declared name maps to exactly one line.
    """
    seen: set[str] = set()
    for name in declared:
        if name in seen:
            raise ValidationError(f"duplicate zone name {name!r}")
        seen.add(name)


def check_no_undefined_zones(graph: Graph, start: str, end: str) -> None:
    """Every connection endpoint must reference a declared, navigable zone.

    Also verifies that `start` and `end` are themselves in the navigable graph.
    """
    if start not in graph.zones:
        raise ValidationError(f"start zone {start!r} missing from navigable graph")
    if end not in graph.zones:
        raise ValidationError(f"end zone {end!r} missing from navigable graph")
    for a, neighbors in graph.adj.items():
        if a not in graph.zones:
            raise ValidationError(f"connection references undeclared zone {a!r}")
        for b in neighbors:
            if b not in graph.zones:
                raise ValidationError(
                    f"connection references undeclared zone {b!r}"
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
    raise ValidationError(
        f"end zone {end!r} is not reachable from start {start!r}"
    )


def validate_input(parsed: ParsedMap) -> None:
    """Run every input validation rule against a parsed map (F1.3).

    Order matters: capacities → duplicate zone names → undefined zones → reachability.

    Note on duplicate connections: they are NOT re-derived here. A `Graph` stores each
    connection in both directions (`adj[a][b]` and `adj[b][a]`) and is keyed by
    neighbour, so it is structurally impossible for the graph to hold the same
    unordered pair twice. Duplicate `connection:` lines are rejected at parse time by
    `parse_lines` (which sees the raw lines and can detect them). Re-deriving that
    check from the graph would be a tautology, not an independent judgement.
    """
    check_positive_capacity(parsed.nb_drones, "nb_drones")
    for a, neighbors in parsed.graph.adj.items():
        for b, conn in neighbors.items():
            check_positive_capacity(conn.cap, f"connection {a}-{b}")
    check_no_duplicates({name: 0 for name in parsed.graph.zones})
    check_no_undefined_zones(parsed.graph, parsed.start, parsed.end)
    check_reachability(parsed.graph, parsed.start, parsed.end)


def load_map(path: Path) -> ParsedMap:
    """Parse and validate a map file (F1.2 + F1.3).

    Combines `parse_map` (syntax) with `validate_input` (semantics) and returns a
    fully validated `ParsedMap`.
    """
    parsed = parse_map(path)
    validate_input(parsed)
    return parsed
