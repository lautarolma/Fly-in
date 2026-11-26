"""End-to-end coverage over the 9 mandatory maps: CLI → plan → simulate → trace."""

from __future__ import annotations

from pathlib import Path

import pytest

from flyin.cli import main
from flyin.parsing.input_rules import load_map
from tests.trace import assert_trace_respects_caps

MANDATORY_MAPS = sorted(
    path.relative_to("maps")
    for path in Path("maps").glob("*/*.txt")
    if "challenger" not in path.parts
)


@pytest.mark.parametrize("map_path", MANDATORY_MAPS)
def test_mandatory_map_runs_and_respects_caps(
    map_path: Path,
    maps_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """F3.5/F3.6/F5: el CLI entrega la flota y la traza no viola capacidades."""
    map_file = maps_dir / map_path
    parsed = load_map(map_file)

    assert main([str(map_file)]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    lines = captured.out.splitlines()
    assert lines

    drone_ids = [f"D{n}" for n in range(1, parsed.nb_drones + 1)]
    final = assert_trace_respects_caps(
        parsed.graph, lines, start=parsed.start, drone_ids=drone_ids
    )
    assert set(final.values()) == {parsed.end}
