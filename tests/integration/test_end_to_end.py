"""End-to-end tests over the official maps (filled in as F1+ land)."""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="pipeline not implemented yet (F1+)")
def test_easy_map_runs_and_validates(maps_dir: object) -> None:
    """Parse → plan → simulate → validate the easy map; assert a valid schedule."""
