"""F4.1: the formatter owns every character of the official output syntax."""

from __future__ import annotations

import pytest

from flyin.domain.connection import Connection
from flyin.domain.drone import Drone
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone
from flyin.rendering.formatter import format_turn, move_token, transit_token
from flyin.simulation.simulator import Simulation


def test_format_turn_joins_with_single_spaces_and_no_prefix() -> None:
    """D5: la línea arranca con un token y no lleva número de turno."""
    assert format_turn(["D1-roof1", "D2-corridorA"]) == "D1-roof1 D2-corridorA"


def test_format_turn_empty() -> None:
    """Un turno sin movimientos no produce texto."""
    assert format_turn([]) == ""


def test_move_token_exact() -> None:
    """REQ-OUT-1: `D<id>-<zona>`."""
    assert move_token("D1", "roof1") == "D1-roof1"


def test_transit_token_exact() -> None:
    """D1: `D<id>-<origen>-<destino>`, en dirección de viaje."""
    assert transit_token("D1", "roof1", "tunnelB") == "D1-roof1-tunnelB"


def test_simulation_delegates_token_syntax_to_formatter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A6: el simulador no arma strings de salida por su cuenta."""
    graph = Graph()
    graph.add_zone(Zone("start", 0, 0, cap=None))
    graph.add_zone(Zone("end", 1, 0, cap=None))
    graph.add_connection(Connection("start", "end"))
    monkeypatch.setattr(
        "flyin.simulation.simulator.move_token",
        lambda drone_id, zone: f"<{drone_id}->{zone}>",
    )
    drone = Drone(id="D1", route=("start", "end"))
    assert Simulation(graph, [drone], "end").run() == ["<D1->end>"]
