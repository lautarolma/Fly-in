"""F3.2: turn loop, restricted transit, release-before-reserve and output."""

from __future__ import annotations

from flyin.domain.connection import Connection
from flyin.domain.drone import Drone, DroneState
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone, ZoneType
from flyin.pathfinding.dijkstra import DijkstraPathFinder
from flyin.simulation.reservation_table import ReservationTable
from flyin.simulation.simulator import Simulation


def _graph(*zones: Zone, links: tuple[tuple[str, str, int], ...] = ()) -> Graph:
    graph = Graph()
    for zone in zones:
        graph.add_zone(zone)
    for a, b, cap in links:
        graph.add_connection(Connection(a=a, b=b, cap=cap))
    return graph


def test_single_normal_move_delivers_in_one_turn() -> None:
    """Un salto normal despega y aterriza en el mismo turno (I4)."""
    graph = _graph(
        Zone("start", 0, 0, cap=None),
        Zone("end", 1, 0, cap=None),
        links=(("start", "end", 1),),
    )
    drone = Drone(id="D1", route=("start", "end"))
    lines = Simulation(graph, [drone], "end").run()
    assert lines == ["D1-end"]
    assert drone.is_delivered
    assert drone.waypoint_index == 1


def test_deadlock_emits_no_empty_line() -> None:
    """Sin movimientos y sin tránsito: corte limpio (I9)."""
    graph = _graph(Zone("start", 0, 0, cap=None), Zone("end", 1, 0, cap=None))
    drone = Drone(id="D1", route=("start", "end"))
    assert Simulation(graph, [drone], "end").run() == []
    assert not drone.is_delivered


def test_restricted_transit_two_turns() -> None:
    """Despegue con token de conexión y llegada forzada al turno siguiente."""
    graph = _graph(
        Zone("start", 0, 0, cap=None),
        Zone("tunnel", 1, 0, type=ZoneType.RESTRICTED, cap=1),
        Zone("end", 2, 0, cap=None),
        links=(("start", "tunnel", 1), ("tunnel", "end", 1)),
    )
    drone = Drone(id="D1", route=("start", "tunnel", "end"))
    lines = Simulation(graph, [drone], "end").run()
    assert lines == ["D1-start-tunnel", "D1-tunnel D1-end"]
    assert drone.is_delivered


def test_restricted_link_stays_blocked_on_arrival_turn() -> None:
    """D2b: la ventana [t, t+1] sigue ocupada cuando D1 aterriza."""
    graph = _graph(
        Zone("start", 0, 0, cap=None),
        Zone("tunnel", 1, 0, type=ZoneType.RESTRICTED, cap=1),
        Zone("end", 2, 0, cap=None),
        links=(("start", "tunnel", 1), ("tunnel", "end", 1)),
    )
    drones = [
        Drone(id="D1", route=("start", "tunnel", "end")),
        Drone(id="D2", route=("start", "tunnel", "end")),
    ]
    lines = Simulation(graph, drones, "end").run()
    assert lines == [
        "D1-start-tunnel",
        "D1-tunnel D1-end",
        "D2-start-tunnel",
        "D2-tunnel D2-end",
    ]
    assert all(drone.is_delivered for drone in drones)


def test_zone_capacity_releases_leaver_before_reserving_arrival() -> None:
    """D1 libera `roof` en t=2 y D2 entra en el mismo turno."""
    graph = _graph(
        Zone("start", 0, 0, cap=None),
        Zone("roof", 1, 0, cap=1),
        Zone("end", 2, 0, cap=None),
        links=(("start", "roof", 1), ("roof", "end", 1)),
    )
    drones = [
        Drone(id="D1", route=("start", "roof", "end")),
        Drone(id="D2", route=("start", "roof", "end")),
    ]
    lines = Simulation(graph, drones, "end").run()
    assert lines == ["D1-roof", "D1-end D2-roof", "D2-end"]


def test_swap_allowed_with_cap_two_link() -> None:
    """REQ-SWAP-1: A↔B necesita cap(link)≥2, no cap=1."""
    graph = _graph(
        Zone("A", 0, 0, cap=1),
        Zone("B", 1, 0, cap=1),
        Zone("end", 2, 0, cap=None),
        links=(("A", "B", 2), ("A", "end", 1), ("B", "end", 1)),
    )
    drones = [
        Drone(id="D1", route=("A", "B", "end")),
        Drone(id="D2", route=("B", "A", "end")),
    ]
    lines = Simulation(graph, drones, "end").run()
    assert lines == ["D1-B D2-A", "D1-end D2-end"]
    assert all(drone.is_delivered for drone in drones)


def test_output_is_sorted_by_numeric_id() -> None:
    """D2 va antes que D10 aunque lexicográficamente sería al revés."""
    graph = _graph(
        Zone("start", 0, 0, cap=None),
        Zone("end", 1, 0, cap=None),
        links=(("start", "end", 5),),
    )
    drones = [Drone(id=f"D{n}", route=("start", "end")) for n in (2, 10)]
    lines = Simulation(graph, drones, "end").run()
    assert lines == ["D2-end D10-end"]


def _restricted_graph() -> Graph:
    """start → tunnel(restricted) → end, con cap 1 en ambos links."""
    return _graph(
        Zone("start", 0, 0, cap=None),
        Zone("tunnel", 1, 0, type=ZoneType.RESTRICTED, cap=1),
        Zone("end", 2, 0, cap=None),
        links=(("start", "tunnel", 1), ("tunnel", "end", 1)),
    )


def test_transit_full_period_blocks_both_turns() -> None:
    """D2b default: la ventana [t, t+1] sigue ocupada al aterrizar (I11)."""
    table = ReservationTable(prune_link_history=False)
    drones = [
        Drone(id="D1", route=("start", "tunnel", "end")),
        Drone(id="D2", route=("start", "tunnel", "end")),
    ]
    lines = Simulation(_restricted_graph(), drones, "end", table=table).run()
    assert lines == [
        "D1-start-tunnel",
        "D1-tunnel D1-end",
        "D2-start-tunnel",
        "D2-tunnel D2-end",
    ]
    assert table.link_usage(("start", "tunnel"), 2) == 1


def test_takeoff_only_flag_pipelines_next_drone() -> None:
    """D2b=False: el link se libera en la llegada y D2 despega en ese turno."""
    drones = [
        Drone(id="D1", route=("start", "tunnel", "end")),
        Drone(id="D2", route=("start", "tunnel", "end")),
    ]
    lines = Simulation(
        _restricted_graph(), drones, "end", transit_occupies_full_period=False
    ).run()
    assert lines == [
        "D1-start-tunnel",
        "D1-tunnel D1-end D2-start-tunnel",
        "D2-tunnel D2-end",
    ]
    assert all(drone.is_delivered for drone in drones)


def test_arrival_reserved_at_departure() -> None:
    """I5: la llegada forzada prometida ocupa el único cupo de `tunnel`."""
    graph = _graph(
        Zone("start", 0, 0, cap=None),
        Zone("tunnel", 1, 0, type=ZoneType.RESTRICTED, cap=1),
        links=(("start", "tunnel", 1),),
    )
    drones = [
        Drone(id="D1", route=("start", "tunnel")),
        Drone(id="D2", route=("start", "tunnel")),
    ]
    lines = Simulation(graph, drones, "tunnel").run()
    assert lines == ["D1-start-tunnel", "D1-tunnel"]
    assert drones[0].is_delivered
    assert not drones[1].is_delivered


def test_landing_consumes_turn() -> None:
    """I10: el aterrizaje es un evento del turno t+1, no del despegue."""
    graph = _restricted_graph()
    drone = Drone(id="D1", route=("start", "tunnel", "end"))
    simulation = Simulation(graph, [drone], "end")
    distances = DijkstraPathFinder().distances_to(graph, "end")

    simulation.table.reserve_zone("start", 1)
    assert simulation._run_turn(1, distances) == [("D1", "D1-start-tunnel")]
    assert drone.transit_turns_left == 1
    simulation._close_turn(1)

    assert simulation._run_turn(2, distances) == [
        ("D1", "D1-tunnel"),
        ("D1", "D1-end"),
    ]
    assert drone.state is DroneState.DELIVERED
    assert drone.transit_turns_left == 0
    assert simulation.table.pending("tunnel") == 0


def test_end_hub_restricted_two_turns() -> None:
    """A9: `end_hub` restricted cuesta 2 pero no tiene límite de capacidad."""
    graph = _graph(
        Zone("start", 0, 0, cap=None),
        Zone("end", 1, 0, type=ZoneType.RESTRICTED, cap=None),
        links=(("start", "end", 1),),
    )
    drone = Drone(id="D1", route=("start", "end"))
    simulation = Simulation(graph, [drone], "end")
    assert simulation.run() == ["D1-start-end", "D1-end"]
    assert drone.is_delivered
    assert simulation.table.can_reserve_zone("end", 2, None)
