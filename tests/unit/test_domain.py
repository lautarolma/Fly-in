"""Domain invariants: immutability, canonical keys, capacities (F1.1/F3.1)."""

from __future__ import annotations

import dataclasses

import pytest

from flyin.domain.connection import Connection, connection_key
from flyin.domain.graph import Graph
from flyin.domain.drone import Drone, DroneState, make_fleet
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
    assert drones1[1].id == "D2"
    assert drones1[0].route == ("start",)
    assert drones1[0].waypoint_index == 0
    assert drones1[0].state is DroneState.WAITING
    assert drones1[0].target is None
    assert drones1[0].transit_turns_left == 0
    assert drones2[0].id == "D1"
    assert drones2[0].route == ("start",)
    # Las flotas son objetos distintos
    assert drones1 is not drones2


def test_make_fleet_nb_drones_0() -> None:
    """make_fleet(0, start) devuelve lista vacía."""
    drones = make_fleet(0, "start")
    assert drones == []


def test_drone_route_is_an_immutable_tuple() -> None:
    """La ruta es una tupla: nadie la muta desde afuera (F3.1)."""
    drone = Drone(id="D1", route=("start", "end"))
    assert isinstance(drone.route, tuple)
    assert drone.route == ("start", "end")


def test_drone_cursor_reads_current_and_next_zone() -> None:
    """El cursor O(1) lee la zona actual y el siguiente waypoint."""
    drone = Drone(id="D1", route=("start", "hub", "end"), waypoint_index=1)
    assert drone.current_zone == "hub"
    assert drone.next_zone == "end"
    assert not drone.route_exhausted


def test_drone_route_exhausted_is_not_the_same_as_delivered() -> None:
    """Agotar la ruta no implica estar entregado: manda el estado FSM."""
    drone = Drone(id="D1", route=("start", "end"), waypoint_index=1)
    assert drone.next_zone is None
    assert drone.route_exhausted
    assert not drone.is_delivered
    drone.state = DroneState.DELIVERED
    assert drone.is_delivered


def test_drone_transit_fields_are_inactive_by_default() -> None:
    """I1: WAITING implica target=None y transit_turns_left=0."""
    drone = Drone(id="D1", route=("start",))
    assert drone.state is DroneState.WAITING
    assert drone.target is None
    assert drone.transit_turns_left == 0


def test_drone_in_transit_keeps_turns_left() -> None:
    """I1: IN_TRANSIT implica transit_turns_left > 0."""
    drone = Drone(
        id="D1",
        route=("hub", "roof1"),
        state=DroneState.IN_TRANSIT,
        target="roof1",
        transit_turns_left=1,
    )
    assert drone.state is DroneState.IN_TRANSIT
    assert drone.target == "roof1"
    assert drone.transit_turns_left > 0
