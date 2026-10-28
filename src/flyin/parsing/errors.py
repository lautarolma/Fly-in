"""Parsing and input-validation errors, always reporting line and cause (REQ-VALID-1, REQ-ERR-1)."""

from __future__ import annotations


class MapError(Exception):
    """Base class for every input problem (syntax or validation)."""

    def __init__(self, message: str, line: int | None = None) -> None:
        self.line = line
        where = f"line {line}: " if line is not None else ""
        super().__init__(f"{where}{message}")


class ParseError(MapError):
    """A syntactically invalid map line."""


class ValidationError(MapError):
    """A structurally parseable map that violates a rule."""
