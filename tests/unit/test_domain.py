"""Domain invariants: immutability, canonical keys, capacities (F1.1)."""

from __future__ import annotations

import dataclasses

import pytest

from flyin.domain.connection import Connection, connection_key
from flyin.domain.graph import Graph
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
