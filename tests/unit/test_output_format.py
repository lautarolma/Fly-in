"""F4.2: byte-exact golden output and the D1 transit token."""

from __future__ import annotations

from pathlib import Path

import pytest

from flyin.cli import main
from flyin.domain.connection import Connection
from flyin.domain.drone import Drone
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone, ZoneType
from flyin.simulation.simulator import Simulation

GOLDEN_EASY = {
    "01_linear_path.txt": (
        "D1-waypoint1\n"
        "D1-waypoint2 D2-waypoint1\n"
        "D1-goal D2-waypoint2\n"
        "D2-goal\n"
    ),
    "02_simple_fork.txt": (
        "D1-junction D2-junction\n"
        "D1-path_a D2-path_b D3-junction D4-junction\n"
        "D1-goal D2-goal D3-path_a D4-path_b\n"
        "D3-goal D4-goal\n"
    ),
    "03_basic_capacity.txt": (
        "D1-bottleneck D2-bottleneck\n"
        "D1-wide_area D2-wide_area D3-bottleneck D4-bottleneck\n"
        "D1-goal D2-goal D3-wide_area D4-wide_area\n"
        "D3-goal D4-goal\n"
    ),
}


@pytest.mark.parametrize(("map_name", "expected"), sorted(GOLDEN_EASY.items()))
def test_easy_matches_golden_bytes(
    map_name: str,
    expected: str,
    maps_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """REQ-OUT-1: stdout coincides byte a byte con la salida esperada."""
    assert main([str(maps_dir / "easy" / map_name)]) == 0
    captured = capsys.readouterr()
    assert captured.out == expected
    assert captured.err == ""
    assert all(line.startswith("D") for line in expected.splitlines())


def test_output_connection_token() -> None:
    """D1: despegue `D1-roof1-tunnelB` y llegada `D1-tunnelB`."""
    graph = Graph()
    graph.add_zone(Zone("roof1", 0, 0, cap=None))
    graph.add_zone(Zone("tunnelB", 1, 0, type=ZoneType.RESTRICTED, cap=1))
    graph.add_zone(Zone("goal", 2, 0, cap=None))
    graph.add_connection(Connection("roof1", "tunnelB"))
    graph.add_connection(Connection("tunnelB", "goal"))
    drone = Drone(id="D1", route=("roof1", "tunnelB", "goal"))
    assert Simulation(graph, [drone], "goal").run() == [
        "D1-roof1-tunnelB",
        "D1-tunnelB D1-goal",
    ]


def test_output_omits_waiting_drones() -> None:
    """REQ-OUT-1: D2 espera en el primer turno y no aparece en esa línea."""
    graph = Graph()
    graph.add_zone(Zone("start", 0, 0, cap=None))
    graph.add_zone(Zone("mid", 1, 0, cap=2))
    graph.add_zone(Zone("goal", 2, 0, cap=None))
    graph.add_connection(Connection("start", "mid", cap=1))
    graph.add_connection(Connection("mid", "goal"))
    drones = [
        Drone(id="D1", route=("start", "mid", "goal")),
        Drone(id="D2", route=("start", "mid", "goal")),
    ]
    lines = Simulation(graph, drones, "goal").run()
    assert lines == ["D1-mid", "D1-goal D2-mid", "D2-goal"]
    assert "D2" not in lines[0]
