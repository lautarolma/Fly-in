"""End-to-end coverage over the official easy maps: CLI → plan → simulate → trace."""

from __future__ import annotations

from pathlib import Path

import pytest

from flyin.cli import main
from flyin.parsing.input_rules import load_map
from tests.trace import assert_trace_respects_caps

EASY_MAPS = ("01_linear_path.txt", "02_simple_fork.txt", "03_basic_capacity.txt")


@pytest.mark.parametrize("map_name", EASY_MAPS)
def test_easy_map_runs_and_respects_caps(
    map_name: str,
    maps_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """F3.5/F3.6: el CLI entrega la flota y la traza no viola capacidades."""
    map_path = maps_dir / "easy" / map_name
    parsed = load_map(map_path)

    assert main([str(map_path)]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    lines = captured.out.splitlines()
    assert lines

    drone_ids = [f"D{n}" for n in range(1, parsed.nb_drones + 1)]
    final = assert_trace_respects_caps(
        parsed.graph, lines, start=parsed.start, drone_ids=drone_ids
    )
    assert set(final.values()) == {parsed.end}
