"""JUEZ 2: independent auditor of a produced schedule (F7).

Re-derives every rule from scratch and shares NO logic with the simulator. Input validation
is a different concern and lives in `parsing`. The only evidence consumed here is the
official output (`lines`) plus immutable map facts carried by `ParsedMap`.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from flyin.domain.connection import connection_key
from flyin.domain.graph import Graph
from flyin.domain.zone import ZoneType
from flyin.parsing.parser import ParsedMap


class ScheduleError(RuntimeError):
    """El schedule auditado viola una o más reglas del dominio."""


@dataclass(frozen=True, slots=True)
class _Token:
    """Un token de salida ya parseado por el juez."""

    drone_id: str
    origin: str | None
    destination: str
    is_transit: bool
    is_landing: bool


@dataclass(frozen=True, slots=True)
class _Turn:
    """Estado de un turno re-derivado desde su línea."""

    number: int
    raw: str
    tokens: tuple[_Token, ...]
    departures: dict[str, tuple[str, str]]
    leavings: dict[str, tuple[str, str]]
    landings: dict[str, str]
    end_positions: dict[str, str]


@dataclass(frozen=True, slots=True)
class _Trace:
    """Schedule completo re-derivado: la evidencia que consultan todos los checks."""

    lines: tuple[str, ...]
    turns: tuple[_Turn, ...]
    final_positions: dict[str, str]
    drone_ids: tuple[str, ...]
    start: str
    end: str
    link_usage: dict[tuple[tuple[str, str], int], int]
    structural_errors: tuple[str, ...]


class Validator:
    """Re-deriva las reglas y audita cada turno de un schedule."""

    def __init__(
        self, parsed: ParsedMap, *, transit_occupies_full_period: bool = True
    ) -> None:
        self.graph: Graph = parsed.graph
        self.start: str = parsed.start
        self.end: str = parsed.end
        self.nb_drones: int = parsed.nb_drones
        self.drone_ids: tuple[str, ...] = tuple(
            f"D{index}" for index in range(1, parsed.nb_drones + 1)
        )
        self.transit_occupies_full_period = transit_occupies_full_period

    # --- Re-derivación (la ÚNICA lectura de las líneas) -------------------
    def _rederive(self, lines: list[str]) -> _Trace:
        """Reconstruir posiciones, aterrizajes y uso de links sin tocar el simulador."""
        positions: dict[str, str] = {drone: self.start for drone in self.drone_ids}
        # Los despegues de un turno son los aterrizajes OBLIGATORIOS del siguiente.
        pending_landings: dict[str, tuple[str, str]] = {}
        link_usage: dict[tuple[tuple[str, str], int], int] = defaultdict(int)
        turns: list[_Turn] = []
        structural_errors: list[str] = []

        for turn, raw in enumerate(lines, start=1):
            if not raw:
                structural_errors.append(f"empty line at turn {turn}")
                turns.append(_Turn(turn, raw, (), {}, {}, {}, dict(positions)))
                continue
            if raw.startswith("turn "):
                structural_errors.append(f"turn prefix at turn {turn}")

            departures: dict[str, tuple[str, str]] = {}
            leavings: dict[str, tuple[str, str]] = {}
            landings: dict[str, str] = {}
            landed: set[str] = set()
            appearances: dict[str, int] = defaultdict(int)
            tokens: list[_Token] = []

            for piece in raw.split():
                parts = piece.split("-")
                if len(parts) not in (2, 3):
                    structural_errors.append(f"bad token {piece!r} at turn {turn}")
                    continue
                drone_id = parts[0]
                if drone_id not in self.drone_ids:
                    structural_errors.append(
                        f"unknown drone {drone_id!r} at turn {turn}"
                    )
                    continue
                appearances[drone_id] += 1
                # Un dron puede emitir dos tokens: aterrizaje forzado + salida
                # inmediata en el MISMO turno (simulator.py:83-85). Nada más.
                if appearances[drone_id] > 1 and (
                    drone_id not in landed or appearances[drone_id] > 2
                ):
                    structural_errors.append(
                        f"drone {drone_id!r} appears twice at turn {turn}"
                    )
                    continue

                if len(parts) == 3:
                    origin, destination = parts[1], parts[2]
                    if destination not in self.graph.zones:
                        structural_errors.append(
                            f"unknown zone {destination!r} at turn {turn}"
                        )
                        continue
                    if self.graph.zones[destination].type is not ZoneType.RESTRICTED:
                        structural_errors.append(
                            f"transit to non-restricted {destination!r} at turn {turn}"
                        )
                        continue
                    if drone_id in pending_landings:
                        if drone_id not in landed:
                            structural_errors.append(
                                f"{drone_id} skipped its landing at turn {turn}"
                            )
                            continue
                        pending_landings.pop(drone_id)
                    if positions[drone_id] != origin:
                        structural_errors.append(
                            f"{drone_id} departs from {origin!r} but was at "
                            f"{positions[drone_id]!r} at turn {turn}"
                        )
                        continue
                    key = connection_key(origin, destination)
                    departures[drone_id] = (origin, destination)
                    leavings[drone_id] = (origin, destination)
                    link_usage[(key, turn)] += 1
                    if self.transit_occupies_full_period:
                        link_usage[(key, turn + 1)] += 1
                    tokens.append(_Token(drone_id, origin, destination, True, False))
                    # En tránsito NO ocupa la zona destino todavía (trace.py:88).
                    continue

                destination = parts[1]
                if destination not in self.graph.zones:
                    structural_errors.append(
                        f"unknown zone {destination!r} at turn {turn}"
                    )
                    continue
                is_landing = drone_id in pending_landings
                if is_landing:
                    _origin, promised = pending_landings.pop(drone_id)
                    if promised != destination:
                        structural_errors.append(
                            f"{drone_id} landed in {destination!r}, promised "
                            f"{promised!r} at turn {turn}"
                        )
                    landings[drone_id] = destination
                    landed.add(drone_id)
                    tokens.append(_Token(drone_id, None, destination, False, True))
                else:
                    origin = positions[drone_id]
                    if destination not in self.graph.neighbors(origin):
                        structural_errors.append(
                            f"{drone_id}: {origin!r} and {destination!r} are not "
                            f"connected at turn {turn}"
                        )
                        continue
                    key = connection_key(origin, destination)
                    leavings[drone_id] = (origin, destination)
                    link_usage[(key, turn)] += 1
                    tokens.append(_Token(drone_id, origin, destination, False, False))
                positions[drone_id] = destination

            if pending_landings:
                structural_errors.append(f"forced landing missing at turn {turn}")
                pending_landings.clear()

            turns.append(
                _Turn(
                    turn,
                    raw,
                    tuple(tokens),
                    departures,
                    leavings,
                    landings,
                    dict(positions),
                )
            )
            # El pending que queda para el SIGUIENTE turno son los despegues de hoy.
            pending_landings = dict(departures)

        if pending_landings:
            structural_errors.append("trace ends with a drone still in transit")

        return _Trace(
            lines=tuple(lines),
            turns=tuple(turns),
            final_positions=dict(positions),
            drone_ids=self.drone_ids,
            start=self.start,
            end=self.end,
            link_usage=dict(link_usage),
            structural_errors=tuple(structural_errors),
        )

    def _occupancy(self, turn: _Turn) -> dict[str, int]:
        """Ocupación al cierre del turno: quien SALIÓ ya liberó su zona (swap)."""
        occupancy: dict[str, int] = defaultdict(int)
        for drone_id, zone in turn.end_positions.items():
            if drone_id in turn.departures:
                continue
            occupancy[zone] += 1
        return dict(occupancy)

    # --- Checks especialistas --------------------------------------------
    def check_output_coherence(self, lines: list[str]) -> list[str]:
        """Formato oficial: sin prefijo, línea no vacía, tokens válidos, entregados mudos."""
        trace = self._rederive(lines)
        violations = list(trace.structural_errors)
        delivered_at: dict[str, int] = {}
        for turn in trace.turns:
            for drone_id, zone in turn.end_positions.items():
                if zone == self.end and drone_id not in delivered_at:
                    delivered_at[drone_id] = turn.number
        for turn in trace.turns:
            for piece in turn.raw.split():
                drone_id = piece.split("-")[0]
                if drone_id in delivered_at and turn.number > delivered_at[drone_id]:
                    violations.append(
                        f"{drone_id} re-emitido después de entregarse en el turno "
                        f"{delivered_at[drone_id]}"
                    )
        return violations

    def check_all_delivered(self, lines: list[str]) -> list[str]:
        """La flota completa debe terminar en el `end_hub`."""
        trace = self._rederive(lines)
        return [
            f"{drone_id} no terminó en {self.end!r}"
            for drone_id in trace.drone_ids
            if trace.final_positions.get(drone_id) != self.end
        ]

    def check_deadlock(self, lines: list[str]) -> list[str]:
        """Un turno sin movimientos no debe emitir línea ni cortar antes de entregar."""
        trace = self._rederive(lines)
        if not trace.lines:
            return (
                []
                if not trace.drone_ids
                else ["schedule vacío con drones por entregar (deadlock)"]
            )
        undelivered = [
            drone_id
            for drone_id in trace.drone_ids
            if trace.final_positions.get(drone_id) != self.end
        ]
        if undelivered:
            return [
                "la simulación terminó antes de entregar: " + ", ".join(undelivered)
            ]
        return []

    def check_zone_capacity(self, lines: list[str]) -> list[str]:
        """Ninguna zona con cupo excede su `max_drones` al cierre del turno."""
        trace = self._rederive(lines)
        violations: list[str] = []
        for turn in trace.turns:
            for zone, used in self._occupancy(turn).items():
                cap = self.graph.zones[zone].cap
                if cap is not None and used > cap:
                    violations.append(
                        f"zona {zone!r} sobre capacidad en el turno {turn.number}: "
                        f"{used} > {cap}"
                    )
        return violations

    def check_link_capacity_per_turn(self, lines: list[str]) -> list[str]:
        """Cada conexión respeta su cupo en TODA la ventana de tránsito."""
        trace = self._rederive(lines)
        violations: list[str] = []
        for (a, b), turn in sorted(trace.link_usage, key=lambda item: (item[1], item[0])):
            used = trace.link_usage[((a, b), turn)]
            connection = self.graph.connection(a, b)
            if used > connection.cap:
                violations.append(
                    f"conexión {connection.a}-{connection.b} sobre capacidad en el "
                    f"turno {turn}: {used} > {connection.cap}"
                )
        return violations

    def check_start_end_uncapped(self, lines: list[str]) -> list[str]:
        """`start_hub` y `end_hub` son la única excepción al cupo de zona."""
        del lines
        violations: list[str] = []
        for zone in (self.start, self.end):
            cap = self.graph.zones[zone].cap
            if cap is not None:
                violations.append(f"{zone!r} debería estar sin límite de capacidad")
        return violations

    def check_leaver_frees_capacity(self, lines: list[str]) -> list[str]:
        """El cupo se evalúa DESPUÉS de liberar quienes salen: el swap es legal."""
        trace = self._rederive(lines)
        violations: list[str] = []
        for index, turn in enumerate(trace.turns):
            previous = trace.turns[index - 1].end_positions if index else {}
            previous_turn = trace.turns[index - 1] if index else None
            start_occupancy: dict[str, int] = defaultdict(int)
            if previous_turn is None:
                for drone_id in trace.drone_ids:
                    start_occupancy[self.start] += 1
            else:
                # Un dron que despegó hacia restricted NO ocupaba zona al cierre
                # del turno anterior: no debe contarse dos veces (trace.py:92-96).
                for zone, used in self._occupancy(previous_turn).items():
                    start_occupancy[zone] = used
            entrants: dict[str, int] = defaultdict(int)
            for token in turn.tokens:
                if token.is_transit:
                    continue
                if previous.get(token.drone_id, self.start) != token.destination:
                    entrants[token.destination] += 1
            for zone, cap in (
                (name, z.cap) for name, z in self.graph.zones.items() if z.cap is not None
            ):
                leavers = sum(
                    1 for origin, _dest in turn.leavings.values() if origin == zone
                )
                used = start_occupancy[zone] - leavers + entrants[zone]
                if used > cap:
                    violations.append(
                        f"zona {zone!r} sin liberar salidas en el turno {turn.number}: "
                        f"{used} > {cap}"
                    )
        return violations

    def check_restricted_transit(self, lines: list[str]) -> list[str]:
        """Despegue en token de conexión y aterrizaje FORZADO al turno siguiente."""
        trace = self._rederive(lines)
        violations: list[str] = []
        for turn in trace.turns:
            for drone_id, (_origin, destination) in turn.departures.items():
                if turn.number >= len(trace.turns):
                    violations.append(
                        f"{drone_id} quedó en tránsito hacia {destination!r} al "
                        f"terminar el schedule"
                    )
                    continue
                following = trace.turns[turn.number]
                if following.landings.get(drone_id) != destination:
                    violations.append(
                        f"{drone_id} no aterrizó en {destination!r} en el turno "
                        f"{turn.number + 1} (llegada forzada)"
                    )
        return violations

    def check_turn_cost(self, lines: list[str]) -> list[str]:
        """Entrar cuesta según el DESTINO: normal/priority 1, restricted 2."""
        trace = self._rederive(lines)
        violations: list[str] = []
        for turn in trace.turns:
            for token in turn.tokens:
                # El aterrizaje forzado no es una entrada nueva: el costo 2 ya se
                # pagó con el token de tránsito del turno anterior (REQ-TRANSIT-1).
                if token.is_landing:
                    continue
                cost = self.graph.zones[token.destination].type.enter_cost
                if token.is_transit and cost != 2:
                    violations.append(
                        f"{token.drone_id} tránsito hacia {token.destination!r} "
                        f"con costo {cost} (debe ser 2)"
                    )
                elif not token.is_transit and cost != 1:
                    violations.append(
                        f"{token.drone_id} entró a {token.destination!r} "
                        f"con costo {cost} (debe ser 1)"
                    )
        return violations

    def check_blocked_impassable(self, lines: list[str]) -> list[str]:
        """Las zonas `blocked` se podan: ninguna aparece en el grafo navegable."""
        del lines
        return [
            f"zona bloqueada {name!r} no fue podada del grafo navegable"
            for name, zone in self.graph.zones.items()
            if zone.type is ZoneType.BLOCKED
        ]

    def check_phase_commit(self, lines: list[str]) -> list[str]:
        """Coherencia observable del commit: nadie está en dos zonas ni a medio aterrizar."""
        trace = self._rederive(lines)
        return [error for error in trace.structural_errors if " at turn " in error]

    # --- Agregado y gate --------------------------------------------------
    def check(self, lines: list[str]) -> list[str]:
        """Correr TODOS los checks y devolver todas las violaciones (autopsia completa)."""
        checks: tuple[Callable[[list[str]], list[str]], ...] = (
            self.check_output_coherence,
            self.check_all_delivered,
            self.check_deadlock,
            self.check_zone_capacity,
            self.check_link_capacity_per_turn,
            self.check_start_end_uncapped,
            self.check_leaver_frees_capacity,
            self.check_restricted_transit,
            self.check_turn_cost,
            self.check_blocked_impassable,
            self.check_phase_commit,
        )
        found: set[str] = set()
        for check in checks:
            found.update(check(lines))
        return sorted(found)

    def validate(self, lines: list[str]) -> None:
        """Gate del DoD: lanzar `ScheduleError` con el informe completo si algo falla."""
        violations = self.check(lines)
        if violations:
            detail = "\n".join(f"  - {violation}" for violation in violations)
            raise ScheduleError(f"schedule inválido:\n{detail}")
