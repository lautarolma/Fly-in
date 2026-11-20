"""The simulation loop: decide → apply → commit, one line per turn (F3.2)."""

from __future__ import annotations

from dataclasses import dataclass

from flyin.domain.drone import Drone, DroneState
from flyin.domain.graph import Graph
from flyin.pathfinding.dijkstra import DijkstraPathFinder
from flyin.simulation.reservation_table import LinkKey, ReservationTable


@dataclass(frozen=True, slots=True)
class MovementProposal:
    """A single drone's intent for the current turn, ordered by `steps_to_end`."""

    drone_id: str
    origin: str
    destination: str
    key: LinkKey
    enter_cost: int
    steps_to_end: int


def _id_key(drone_id: str) -> tuple[int, str]:
    """Sort D1 < D2 < D10 instead of lexicographic D1 < D10 < D2."""
    try:
        return (int(drone_id[1:]), drone_id)
    except ValueError:
        return (10**9, drone_id)


class Simulation:
    """Advances discrete turns and emits the official movement lines."""

    def __init__(
        self,
        graph: Graph,
        drones: list[Drone],
        end: str,
        table: ReservationTable | None = None,
        transit_occupies_full_period: bool = True,
    ) -> None:
        self.graph = graph
        self.drones = drones
        self.end = end
        self.table = table if table is not None else ReservationTable()
        self.transit_occupies_full_period = transit_occupies_full_period
        self._by_id = {drone.id: drone for drone in drones}

    def run(self) -> list[str]:
        """Simulate until all drones are delivered; return the per-turn lines."""
        distances = DijkstraPathFinder().distances_to(self.graph, self.end)
        for drone in self.drones:
            self.table.reserve_zone(drone.current_zone, 1)

        lines: list[str] = []
        turn = 1
        while not all(drone.is_delivered for drone in self.drones):
            events = self._run_turn(turn, distances)
            in_transit = any(
                drone.state is DroneState.IN_TRANSIT for drone in self.drones
            )
            if not events and not in_transit:
                break  # I9: deadlock, no empty line and no infinite loop.
            if events:
                ordered = sorted(events, key=lambda event: _id_key(event[0]))
                lines.append(" ".join(token for _id, token in ordered))
            self._close_turn(turn)
            turn += 1
        return lines

    # --- P0/P1/P2 ---------------------------------------------------
    def _advance_transit(self, turn: int) -> list[tuple[str, str]]:
        """Land forced arrivals; never release the already-paid link slot."""
        landed: list[tuple[str, str]] = []
        for drone in self.drones:
            if drone.state is not DroneState.IN_TRANSIT:
                continue
            if drone.transit_turns_left <= 0:
                raise RuntimeError(f"{drone.id}: IN_TRANSIT without turns left")
            drone.transit_turns_left -= 1
            if drone.transit_turns_left == 0:
                target = drone.target
                if target is None:
                    raise RuntimeError(f"{drone.id}: IN_TRANSIT without target")
                self._land(drone, target, turn, consume_pending=True)
                landed.append((drone.id, f"{drone.id}-{target}"))
        return landed

    def _proposals(self, distances: dict[str, int]) -> list[MovementProposal]:
        """P2: one intent per WAITING drone that still has a reachable waypoint."""
        proposals: list[MovementProposal] = []
        for drone in self.drones:
            if drone.state is not DroneState.WAITING:
                continue
            destination = drone.next_zone
            if destination is None or destination not in distances:
                continue
            if destination not in self.graph.zones:
                continue
            cost = self.graph.zones[destination].type.enter_cost
            if cost is None:
                continue
            origin = drone.current_zone
            if destination not in self.graph.neighbors(origin):
                continue
            connection = self.graph.connection(origin, destination)
            proposals.append(
                MovementProposal(
                    drone_id=drone.id,
                    origin=origin,
                    destination=destination,
                    key=connection.key,
                    enter_cost=cost,
                    steps_to_end=distances[destination],
                )
            )
        proposals.sort(key=lambda p: (p.steps_to_end, _id_key(p.drone_id)))
        return proposals

    # --- P3/P4 -------------------------------------------------------
    def _run_turn(
        self, turn: int, distances: dict[str, int]
    ) -> list[tuple[str, str]]:
        events = self._advance_transit(turn)
        proposals = self._proposals(distances)

        # Release-before-reserve: free EVERY candidate's origin before checking
        # arrivals, so a swap A↔B can see both slots free in the same turn.
        for proposal in proposals:
            self.table.release_zone(proposal.origin, turn)

        for proposal in proposals:
            if self._approve(proposal, turn):
                events.append((proposal.drone_id, self._departure_token(proposal)))
            else:
                self.table.reserve_zone(proposal.origin, turn)  # rollback: it stays.

        return events

    def _approve(self, proposal: MovementProposal, turn: int) -> bool:
        """Commit one proposal iff zone (incl. promises) and whole window are free."""
        cap = self.graph.zones[proposal.destination].cap
        if not self.table.can_reserve_zone(
            proposal.destination, turn, cap, include_pending=True
        ):
            return False

        connection = self.graph.connection(proposal.origin, proposal.destination)
        restricted = proposal.enter_cost == 2
        # D2b: por default la ventana cubre todo el tránsito; el flag permite medir
        # la variante "sólo despegue". La llegada forzada no depende de esta política.
        window = (
            (turn, turn + 1)
            if restricted and self.transit_occupies_full_period
            else (turn,)
        )
        if not self.table.reserve_link_window(connection.key, window, connection.cap):
            return False

        drone = self._by_id[proposal.drone_id]
        if restricted:
            drone.target = proposal.destination
            drone.transit_turns_left = 1
            drone.state = DroneState.IN_TRANSIT
            self.table.add_pending_arrival(proposal.destination)
        else:
            self._land(drone, proposal.destination, turn, consume_pending=False)
        return True

    def _land(
        self, drone: Drone, target: str, turn: int, *, consume_pending: bool
    ) -> None:
        """Finish the current waypoint and physically occupy `target`."""
        if consume_pending:
            self.table.consume_pending_arrival(target)
        drone.waypoint_index += 1
        drone.target = None
        drone.transit_turns_left = 0
        drone.state = (
            DroneState.DELIVERED if drone.route_exhausted else DroneState.WAITING
        )
        self.table.reserve_zone(target, turn)

    @staticmethod
    def _departure_token(proposal: MovementProposal) -> str:
        if proposal.enter_cost == 2:
            return f"{proposal.drone_id}-{proposal.origin}-{proposal.destination}"
        return f"{proposal.drone_id}-{proposal.destination}"

    def _close_turn(self, turn: int) -> None:
        """Prune link history and seed next turn's occupancy for grounded drones."""
        self.table.close_turn(turn)
        for drone in self.drones:
            if drone.state is not DroneState.IN_TRANSIT:
                self.table.reserve_zone(drone.current_zone, turn + 1)
