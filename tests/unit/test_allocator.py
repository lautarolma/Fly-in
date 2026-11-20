"""F3.6: single-route fleet assignment (Propuesta A)."""

from __future__ import annotations

from flyin.domain.drone import Drone, DroneState, make_fleet
from flyin.pathfinding.base import Path
from flyin.routing.allocator import assign_single_route

ROUTE = Path(zones=("start", "mid", "goal"), cost=2)


def test_assign_single_route_resets_cursor_and_transit_state() -> None:
    """Un dron reutilizado vuelve a WAITING con el cursor en cero."""
    drones = [
        Drone(
            id="D1",
            route=("start",),
            waypoint_index=3,
            state=DroneState.DELIVERED,
            target="old",
            transit_turns_left=2,
        )
    ]
    assigned = assign_single_route(drones, ROUTE)
    assert len(assigned) == 1
    assert assigned[0].id == "D1"
    assert assigned[0].route == ROUTE.zones
    assert assigned[0].waypoint_index == 0
    assert assigned[0].state is DroneState.WAITING
    assert assigned[0].target is None
    assert assigned[0].transit_turns_left == 0
    assert assigned[0].current_zone == "start"
    assert assigned[0].next_zone == "mid"


def test_assign_single_route_does_not_mutate_input() -> None:
    """La asignación es pura: ni la lista ni los drones originales cambian."""
    drones = make_fleet(2, "start")
    assigned = assign_single_route(drones, ROUTE)
    assert [drone.id for drone in assigned] == ["D1", "D2"]
    assert all(drone.route == ROUTE.zones for drone in assigned)
    assert all(assigned[index] is not drones[index] for index in range(2))
    assert [drone.route for drone in drones] == [("start",), ("start",)]


def test_assign_single_route_empty_fleet() -> None:
    """Una flota vacía devuelve una lista vacía, sin efectos."""
    assert assign_single_route([], ROUTE) == []
