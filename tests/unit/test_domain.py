"""Domain invariants: immutability, canonical keys, capacities (F1.1)."""

from __future__ import annotations

import dataclasses

import pytest

from flyin.domain.connection import Connection, connection_key
from flyin.domain.graph import Graph
from flyin.domain.drone import make_fleet
from flyin.domain.drone import DroneState
from flyin.domain.zone import Zone, ZoneType


def test_connection_key_is_order_independent() -> None:
    assert connection_key("a", "b") == connection_key("b", "a")


def test_connection_canonical_key() -> None:
    assert Connection(a="b", b="a").key == ("a", "b")


def test_connection_default_capacity() -> None:
    assert Connection(a="hub", b="roof1").cap == 1


def test_zone_is_frozen() -> None:
    zone = Zone(name="roof1", x=3, y=4, type=ZoneType.RESTRICTED, color="red")
    with pytest.raises(dataclasses.FrozenInstanceError):
        zone.x = 10  # type: ignore[misc]


def test_graph_neighbors_and_connection() -> None:
    graph = Graph()
    graph.add_zone(Zone(name="hub", x=0, y=0))
    graph.add_zone(Zone(name="roof1", x=1, y=0))
    graph.add_connection(Connection(a="hub", b="roof1"))
    assert graph.neighbors("hub") == ["roof1"]
    assert graph.connection("roof1", "hub").key == ("hub", "roof1")


def test_graph_unknown_connection_raises() -> None:
    graph = Graph()
    graph.add_zone(Zone(name="solo", x=0, y=0))
    with pytest.raises(KeyError):
        graph.connection("solo", "nowhere")


def test_zone_enter_cost() -> None:
    """Costo de entrar según el tipo de zona."""
    assert ZoneType.NORMAL.enter_cost == 1
    assert ZoneType.PRIORITY.enter_cost == 1
    assert ZoneType.RESTRICTED.enter_cost == 2
    assert ZoneType.BLOCKED.enter_cost is None


def test_make_fleet_fresh_each_call() -> None:
    """make_fleet devuelve una lista nueva en cada llamada."""
    drones1 = make_fleet(2, "start")
    drones2 = make_fleet(2, "start")
    assert drones1[0].id == "D1"
    assert drones1[0].path == ["start"]
    assert drones1[0].state == DroneState.WAITING
    drones2 = make_fleet(2, "start")
    assert drones2[0].id == "D1"
    assert drones2[0].path == ["start"]
    # Las listas son objetos distintos
    assert drones1 is not drones2


def test_make_fleet_nb_drones_0() -> None:
    """make_fleet(0, start) devuelve lista vacía."""
    drones = make_fleet(0, "start")
    assert drones == []
