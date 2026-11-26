"""F6.4: retry over route subsets and choose the shortest *valid* schedule."""

from __future__ import annotations

from pathlib import Path as FilePath

import pytest

from flyin.domain.connection import Connection
from flyin.domain.graph import Graph
from flyin.domain.zone import Zone, ZoneType
from flyin.parsing.input_rules import load_map
from flyin.pathfinding.base import Path
from flyin.routing.scheduler import Scheduler
from flyin.simulation.simulator import DeadlockError, Simulation


def _graph() -> Graph:
    """Two narrow corridors and one wide restricted corridor to the same goal."""
    graph = Graph()
    graph.add_zone(Zone("start", 0, 0, cap=None))
    graph.add_zone(Zone("hub", 1, 0, cap=1))
    graph.add_zone(Zone("a", 2, 1, cap=1))
    graph.add_zone(Zone("b", 2, -1, cap=1))
    graph.add_zone(Zone("tunnel", 1, 2, type=ZoneType.RESTRICTED, cap=2))
    graph.add_zone(Zone("mid", 2, 2, cap=2))
    graph.add_zone(Zone("end", 3, 0, cap=None))
    for first, second, cap in (
        ("start", "hub", 1),
        ("hub", "a", 1),
        ("a", "end", 1),
        ("hub", "b", 1),
        ("b", "end", 1),
        ("start", "tunnel", 2),
        ("tunnel", "mid", 2),
        ("mid", "end", 2),
    ):
        graph.add_connection(Connection(a=first, b=second, cap=cap))
    return graph


def _candidates() -> list[Path]:
    """The F5 estimate ranks the shared-hub pair first; the wide route wins."""
    return [
        Path(zones=("start", "hub", "a", "end"), cost=3),
        Path(zones=("start", "hub", "b", "end"), cost=3),
        Path(zones=("start", "tunnel", "mid", "end"), cost=4),
    ]


def _inject(
    monkeypatch: pytest.MonkeyPatch, routes: list[Path]
) -> None:
    """Replace only route generation; policy and simulation stay real."""

    def fake_build(
        _self: object,
        _graph: Graph,
        _start: str,
        _goal: str,
        _k: int,
        _nb_drones: int,
    ) -> list[Path]:
        return routes

    monkeypatch.setattr(
        "flyin.routing.scheduler.RouteBuilder.build_for_fleet", fake_build
    )


def test_plan_validated_prefers_shortest_real_schedule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F6.4: measured turns beat the F5 lower bound (4 → 3)."""
    graph = _graph()
    _inject(monkeypatch, _candidates())

    plan = Scheduler().plan_validated(graph, "start", "end", 2)

    assert len(plan.lines) == 3
    assert [drone.route for drone in plan.fleet] == [
        ("start", "tunnel", "mid", "end"),
        ("start", "tunnel", "mid", "end"),
    ]
    assert all(drone.current_zone == "start" for drone in plan.fleet)


def test_plan_validated_skips_deadlocking_subsets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A deadlocking first choice is skipped, never emitted or rendered."""
    graph = Graph()
    graph.add_zone(Zone("start", 0, 0, cap=None))
    graph.add_zone(Zone("trap", 1, 0, cap=1))
    graph.add_zone(Zone("clear", 1, 1, cap=1))
    graph.add_zone(Zone("end", 2, 1, cap=None))
    graph.add_connection(Connection(a="start", b="trap", cap=1))
    graph.add_connection(Connection(a="start", b="clear", cap=1))
    graph.add_connection(Connection(a="clear", b="end", cap=1))
    _inject(
        monkeypatch,
        [
            Path(zones=("start", "trap"), cost=1),
            Path(zones=("start", "clear", "end"), cost=2),
        ],
    )

    plan = Scheduler().plan_validated(graph, "start", "end", 2)

    assert plan.lines == ["D1-clear", "D1-end D2-clear", "D2-end"]
    assert [drone.route for drone in plan.fleet] == [
        ("start", "clear", "end"),
        ("start", "clear", "end"),
    ]


def test_plan_validated_rejects_routes_that_do_not_reach_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A route ending early 'delivers' in the simulator but is not valid."""
    graph = Graph()
    graph.add_zone(Zone("start", 0, 0, cap=None))
    graph.add_zone(Zone("trap", 1, 0, cap=1))
    graph.add_zone(Zone("end", 1, 1, cap=None))
    graph.add_connection(Connection(a="start", b="trap", cap=1))
    graph.add_connection(Connection(a="start", b="end", cap=1))
    _inject(
        monkeypatch,
        [
            Path(zones=("start", "trap"), cost=1),
            Path(zones=("start", "end"), cost=1),
        ],
    )

    plan = Scheduler().plan_validated(graph, "start", "end", 1)

    assert plan.lines == ["D1-end"]
    assert [drone.route for drone in plan.fleet] == [("start", "end")]


def test_plan_validated_raises_when_every_subset_deadlocks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No valid subset means a clear DeadlockError, not an empty success."""
    graph = Graph()
    graph.add_zone(Zone("start", 0, 0, cap=None))
    graph.add_zone(Zone("trap", 1, 0, cap=1))
    graph.add_zone(Zone("end", 1, 1, cap=None))
    graph.add_connection(Connection(a="start", b="trap", cap=1))
    graph.add_connection(Connection(a="start", b="end", cap=1))
    _inject(monkeypatch, [Path(zones=("start", "trap"), cost=1)])

    with pytest.raises(DeadlockError, match="no route selection"):
        Scheduler().plan_validated(graph, "start", "end", 2)


def test_plan_validated_preserves_mandatory_map_schedules(
    maps_dir: FilePath,
) -> None:
    """On current maps the validated winner equals the F5 schedule."""
    for map_file in sorted(FilePath("maps").glob("*/*.txt")):
        if "challenger" in map_file.parts:
            continue
        parsed = load_map(maps_dir / map_file.relative_to("maps"))
        scheduler = Scheduler()
        expected = Simulation(
            parsed.graph,
            scheduler.plan(parsed.graph, parsed.start, parsed.end, parsed.nb_drones),
            parsed.end,
        ).run()
        fresh_f5 = scheduler.plan(
            parsed.graph, parsed.start, parsed.end, parsed.nb_drones
        )
        actual = scheduler.plan_validated(
            parsed.graph, parsed.start, parsed.end, parsed.nb_drones
        )

        assert actual.lines == expected
        assert actual.fleet == fresh_f5


def test_plan_validated_runs_without_visual_observer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validation never calls a turn observer; rendering is CLI-only."""
    seen: list[tuple[int, str]] = []
    graph = _graph()
    _inject(monkeypatch, _candidates())

    plan = Scheduler().plan_validated(graph, "start", "end", 2)
    lines = Simulation(graph, plan.fleet, "end").run(
        on_turn=lambda turn, line: seen.append((turn, line))
    )

    assert lines == plan.lines
    assert [turn for turn, _line in seen] == [1, 2, 3]
