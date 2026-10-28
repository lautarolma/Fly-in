"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

MAPS_DIR = Path(__file__).resolve().parent.parent / "maps"


@pytest.fixture()
def maps_dir() -> Path:
    """Absolute path to the repository's `maps/` directory."""
    return MAPS_DIR
