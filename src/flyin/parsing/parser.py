"""Text map → domain graph. Aborts with line + cause on any problem (REQ-PARSE-1)."""

from __future__ import annotations

from pathlib import Path

from flyin.domain.graph import Graph


def read_lines(path: Path) -> list[str]:
    """Read the raw map lines using a context manager (REQ-ERR-1, closed handle)."""
    raise NotImplementedError


def parse_map(path: Path) -> Graph:
    """Parse the map at `path` into a navigable `Graph` (F1.2)."""
    raise NotImplementedError
