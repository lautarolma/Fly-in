"""F4.3: visual panel uses ANSI on stderr and never on stdout."""

from __future__ import annotations

from io import StringIO

from flyin.domain.connection import Connection
from flyin.domain.drone import Drone, DroneState
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone, ZoneType
from flyin.rendering.renderer import Renderer


def test_render_colored_panel() -> None:
    """REQ-VIS-1: zonas con color, ocupantes tránsito y línea oficial en el panel."""
    graph = Graph()
    graph.add_zone(Zone("start", 0, 0, cap=None, color="green"))
    graph.add_zone(
        Zone("tunnel", 1, 0, type=ZoneType.RESTRICTED, cap=1, color="red")
    )
    graph.add_zone(Zone("goal", 2, 0, cap=None, color="blue"))
    graph.add_connection(Connection("start", "tunnel"))
    graph.add_connection(Connection("tunnel", "goal"))
    drones = [
        Drone(
            id="D1",
            route=("start", "tunnel", "goal"),
            state=DroneState.IN_TRANSIT,
            target="tunnel",
            transit_turns_left=1,
        ),
        Drone(id="D2", route=("start", "tunnel", "goal")),
    ]
    stream = StringIO()

    Renderer(graph, drones, stream).render(1, "D1-start-tunnel")

    out = stream.getvalue()
    assert "\033[32mstart\033[0m [D2]" in out
    assert "\033[31mtunnel\033[0m [-]" in out
    assert "in transit: D1->tunnel" in out
    assert "official: D1-start-tunnel" in out


def test_render_unknown_color_fallback() -> None:
    """REQ-VIS-1: un color desconocido cae al default sin romper el render."""
    graph = Graph()
    graph.add_zone(Zone("weird", 0, 0, color="chartreuse"))
    stream = StringIO()

    Renderer(graph, [], stream).render(1)

    assert "\033[37mweird\033[0m" in stream.getvalue()
