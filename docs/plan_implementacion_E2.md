# Fly-in — Plan de implementación E2

> **Documento VIVO.** Se reestructura durante la implementación, a medida que aparecen planteos
> nuevos. Versión inicial: `v0.1`.
>
> **Rol:** traducir la estructura (ver `plan_estructuracion_E2.md`) en **tareas ejecutables** con
> orden, entregables y criterios de aceptación. El **cuándo** vive en `cronograma_E2.md`.
>
> **Regla transversal:** cada tarea deja **commit(s) atómicos**, **tests verdes** y **lint limpio**
> antes de pasar a la siguiente.

---

## 0. Principios de ejecución

1. **Factibilidad primero:** cada fase deja el programa **corrible y correcto** en los mapas que ya
   soporta. Nunca dejo el repo roto entre fases.
2. **AI-first, humano-al-mando:** los agentes de IA escriben boilerplate, tests y docs; **yo**
   decido algoritmos, invariantes y defensa. (El agente ejecuta, yo dirijo.)
3. **Git granular:** una tarea = uno o varios commits atómicos con **Conventional Commits**
   (`feat:`, `fix:`, `test:`, `chore:`, `docs:`), en branches por feature + PR (espejo de Mario/Jose).
4. **Testeá el invariante, no el happy path:** los 6 invariantes de `plan_estructuracion_E2.md` §9
   tienen test antes de darse por hechos.
5. **El `Validator` es un test de propiedad:** corre sobre cada mapa en cada CI.
6. **Definition of Done global** (aplica a toda tarea): compila, corre, tests verdes,
   `make lint` limpio (flake8 + mypy), docstring donde haga falta, commit convencional.

---

## 1. Fases y tareas

### F0 — Setup, tooling y estudio  _(base de infraestructura)_

| ID | Tarea | Entregable | Deps | Esfuerzo |
|---|---|---|---|---|
| F0.1 | Estudio del modelo (turnos, capacidades, restricted, swap) | Notas de modelo + 3 mapas de prueba a mano | — | 3h |
| F0.2 | Repo skeleton: layout de carpetas + `pyproject.toml` + `uv` | `uv sync` funciona | — | 2h |
| F0.3 | Makefile: `install run debug clean lint lint-strict` (+ `test`) | `make run` / `make lint` andan | F0.2 | 1.5h |
| F0.4 | Config `flake8` + `mypy --strict` + `pytest` | `make lint` limpio en esqueleto vacío | F0.2 | 1.5h |
| F0.5 | CI en GitHub Actions (lint + test), espejo de Jose | PR con CI verde | F0.4 | 1.5h |
| F0.6 | Convención `git`: branches + conventional commits + plantilla PR | Primer PR de ejemplo mergeado | F0.2 | 1h |

**DoD F0:** un push dispara CI que corre lint+test y queda verde.

---

### F1 — Parser + Dominio  _(entrada y modelo)_

| ID | Tarea | Entregable | Deps | Esfuerzo |
|---|---|---|---|---|
| F1.1 | `ZoneType` (Enum) + `Zone` + `Connection` (dataclasses frozen) | Modelo + unit tests | F0 | 2h |
| F1.2 | `Parser` de texto → dominio, con errores **línea + causa** | Parser + tests de error ✅D3 | F1.1 | 3h |
| F1.3 | Validación: 1 start / 1 end, sin duplicados, tipos válidos, caps > 0, `blocked` podado | Suite de validación | F1.2 | 2h |
| F1.4 | Chequeo de **alcanzabilidad** (si `end` aislada → error claro) | Test de grafo desconectado | F1.2 | 1h |
| F1.5 | `Graph`: `neighbors()`, `conn(a,b)` (clave canónica `sorted`) | Grafo + tests | F1.1 | 2h |

**DoD F1:** parseo + validación de un `.txt` válido e inválido, todo con error claro.

---

### F2 — PathFinder  _(búsqueda de caminos)_

| ID | Tarea | Entregable | Deps | Esfuerzo |
|---|---|---|---|---|
| F2.1 | Interfaz `PathFinder` (`ABC`/`Protocol`): `find(graph)` | Interfaz + docstring | F1 | 0.5h |
| F2.2 | **Dijkstra** (heapq) con pesos de vértice `{normal:1, priority:1, restricted:2}` | `DijkstraPathFinder` + tests | F2.1 | 3h |
| F2.3 | **Dijkstra reverso** desde `end` → `dist_to_end` (heurística/tie-break) | `dist_to_end` + tests | F2.2 | 2h |
| F2.4 | **A\*** con `h = dist_to_end` (admisible y consistente) | `AStarPathFinder` (opcional) | F2.3 | 2h |

**DoD F2:** camino más corto correcto en mapas con `restricted` y `priority`, con tie-break.

> **Nota didáctica:** el desempate es **entre igual costo**, preferir `priority`. `priority` **no**
> es peso 0.

---

### F3 — Simulador base (Propuesta A)  _(el corazón)_

| ID | Tarea | Entregable | Deps | Esfuerzo |
|---|---|---|---|---|
| F3.1 | `Drone` + FSM `WAITING/IN_TRANSIT/DELIVERED` | Modelo drone + tests | F1 | 1.5h |
| F3.2 | Loop de turnos con **3 fases**: decidir → aplicar → commit simultáneo | Simulador corriendo | F2 | 3h |
| F3.3 | **Transit restricted**: ocupar conexión durante el tránsito (2 turnos, D2b) + llegada obligada | Test de invariante #1 ✅D2/D2b | F3.2 | 2.5h |
| F3.4 | **Swap**: validar capacidad **después** de liberar salidas | Test de invariante #2 | F3.2 | 2h |
| F3.5 | Capacidades de zona y conexión por turno | Test de invariante #3 | F3.2 | 1.5h |
| F3.6 | Asignación greedy simple (una ruta) | Drones entregados | F3.2 | 1h |

**DoD F3:** Propuesta A corre y entrega los drones en `easy` respetando capacidades y transit.

> **Orden interno crítico:** F3.3 y F3.4 **antes** que F3.5/F3.6. Son los invariantes que más fallan.

---

### F4 — Salida y Render  _(formato que se evalúa)_

| ID | Tarea | Entregable | Deps | Esfuerzo |
|---|---|---|---|---|
| F4.1 | Formateador de líneas por turno, **sin prefijo de número** (D5) | Strings de turno + golden tests ✅D1/D5 | F3 | 2h |
| F4.2 | Token de conexión en tránsito `D<id>-<origen>-<destino>` | Test de formato exacto ✅D1 | F4.1 | 1h |
| F4.3 | Render terminal en color (estado de zonas + drones + línea oficial) | Salida coloreada | F4.1 | 2h |
| F4.4 | Errores y salida con `sys.exit` coherente | Rama de error probada | F4.1 | 0.5h |

**DoD F4:** la salida de `easy` coincide **byte a byte** con el formato esperado.

---

### F5 — K-caminos + Estimador  _(repartir y decidir)_

| ID | Tarea | Entregable | Deps | Esfuerzo |
|---|---|---|---|---|
| F5.1 | `RouteBuilder`: k caminos por **node-disjoint iterado** o **penalización +Δ** | k rutas candidatas + tests ✅D4 | F2 | 3h |
| F5.2 | `k = min(4, N)` y acotado (no explotar la combinatoria) | Test de cotas | F5.1 | 1h |
| F5.3 | `Estimator`: cotas `max(costo_i + carga_i − 1)` y por recurso | Cota + tests vs simulación | F5.1 | 3h |
| F5.4 | Selección del subconjunto de rutas por menor cota estimada | Best selection | F5.3 | 2h |
| F5.5 | Allocator greedy (ETA): drone → ruta que minimiza la cota | Reparto por rutas | F5.4 | 2h |

**DoD F5:** en `medium/hard` el reparto por múltiples rutas **baja el makespan** vs una sola ruta.

> **Checkpoint de re-estimación #1:** si con k-rutas no alcanza para los hard, evaluar Propuesta B
> (MCMF) — ver `comparativa_propuestas.md` §11.

---

### F6 — Scheduler con reservas  _(ejecutar bien)_

| ID | Tarea | Entregable | Deps | Esfuerzo |
|---|---|---|---|---|
| F6.1 | Reservas de capacidad por turno (`(zona,t)` / `(conexión,t)`) | Table + tests ✅D2 | F3 | 2.5h |
| F6.2 | Política: liberar salidas → reservar llegadas (incluye restricted, flag D2b) | Scheduler + tests ✅D2/D2b | F6.1 | 2.5h |
| F6.3 | **Detección de deadlock** del schedule | Excepción clara + test | F6.2 | 2h |
| F6.4 | Reintentos sobre distintas selecciones de rutas | Best valid schedule | F6.3 | 2h |

**DoD F6:** el scheduler produce schedules válidos en los mandatory **sin** intervención manual.

---

### F7 — Validador independiente  _(el juez)_

| ID | Tarea | Entregable | Deps | Esfuerzo |
|---|---|---|---|---|
| F7.1 | `Validator`: re-deriva TODAS las reglas desde cero | Validador + tests | F4, F6 | 3h |
| F7.2 | Chequeos: capacidades, transit, swap, coherencia del output | Tests de propiedad ✅D1/D2 | F7.1 | 2h |
| F7.3 | Integración: correr el validador sobre **todos** los mapas en CI | CI + reporte | F7.1 | 1.5h |

**DoD F7:** ningún schedule se considera válido sin pasar el validador independiente.

> **Aquí se cierra el corazón de E2.** Lo que sigue es pulido y defensa.

---

### F8 — Hardening, benchmarks y defensa

| ID | Tarea | Entregable | Deps | Esfuerzo |
|---|---|---|---|---|
| F8.1 | Benchmark de los mandatory (easy/medium/hard) + registrar turnos | Tabla de resultados ✅D3 | F7 | 2h |
| F8.2 | Iteración de tuning sobre hard (k, política de reparto) | Makespan mejorado | F8.1 | 3h |
| F8.3 | `README` en **inglés** (requisito del subject) + docs internas | README + docs | F7 | 2h |
| F8.4 | `mypy --strict` al 100% + `flake8` limpio | `make lint-strict` verde | F7 | 2h |
| F8.5 | Guion de defensa + ensayo (recorrer §"Para la defensa") | Guion + ensayo cronometrado | F8.3 | 2.5h |

**DoD F8:** `make lint-strict`, `make test`, CI verdes; README en inglés; defensa ensayada.

---

### F9 — Bonus E4 (Space-Time A\*)  _(opcional, post-E2)_

| ID | Tarea | Entregable | Deps | Esfuerzo |
|---|---|---|---|---|
| F9.1 | Estado `(zona, turno)` + acciones `move`/`wait` | Grafo tiempo-expandido | F8 | 3h |
| F9.2 | Reservation table espacio-temporal + holds provisionales | Reservas | F9.1 | 3h |
| F9.3 | A\* espacio-temporal con `h = dist_to_end` + ventana `W` + límite de seguridad | `SpaceTimePathFinder` | F9.2 | 4h |
| F9.4 | Replan por ventana + integración con validador | Challenger medido | F9.3 | 3h |

**DoD F9:** challenger (25 drones) corrido y validado; idealmente **< 45 turnos**.

---

## 2. Matriz de trazabilidad (requisito → tarea → test)

| Requisito del subject | Tarea | Test / verificación |
|---|---|---|
| Parseo correcto + errores claros | F1.2, F1.3 | tests de error |
| Capacidades de zona | F3.5, F7.2 | invariante #3 |
| Capacidades de conexión | F3.5, F7.2 | invariante #3 |
| `restricted` (2 turnos, transit) | F3.3, F7.2 | invariante #1 |
| Swap (libera salida mismo turno) | F3.4, F7.2 | invariante #2 |
| `start`/`end` sin límite | F3.5 | invariante #4 |
| Formato de salida exacto | F4.1, F4.2 | golden tests |
| Alcanzabilidad / no loop infinito | F1.4 | test grafo aislado |
| Minimizar makespan | F5, F6, F8.2 | benchmarks |
| `flake8` + `mypy` | F0.4, F8.4 | `make lint-strict` |
| Makefile (`install/run/debug/clean/lint/lint-strict`) | F0.3 | `make` targets |

---

## 3. Riesgos y mitigaciones

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Bug en `restricted` transit | Alta | Alto | F3.3 primero + validador |
| Perder el swap (validar antes de liberar) | Media | Alto | F3.4 + test dedicado |
| Combinatoria de rutas explota | Media | Medio | acotar `k = min(4, N)` (F5.2) |
| Deadlock en el scheduler | Media | Medio | detección explícita (F6.3) + reintentos |
| Formato de salida mal interpretado | Media | Alto | cerrar decisión abierta + golden tests |
| Sobrecarga por sobre-ingeniería | Media | Medio | §8 de `plan_estructuracion_E2.md` |
| Recalcular caminos cada turno (timeout) | Media | Alto | cachear 1 vez (F2) |
| `mypy --strict` se vuelve un infierno | Media | Bajo | tipar desde el día 1 (F0.4) |

---

## 4. Puntos de revisión del plan (dónde lo reestructuramos)

- **Fin de F0:** ¿el tooling no molesta? Si el setup se estira, recortar CI a solo lint.
- **Fin de F3:** ¿Propuesta A ya aprueba los mandatory? Si sí, F5-F7 son puro refinamiento.
- **Fin de F5 (Checkpoint #1):** ¿k-rutas alcanza? Si no → evaluar MCMF (B). Si sobra → directo a E4.
- **Fin de F7:** ¿el validador cubre todo? Si aparece un invariante no cubierto, **volver a
  `plan_estructuracion_E2.md` §9** y actualizar.
- **Fin de F8:** decisión go/no-go sobre el bonus E4 según días disponibles.

---

## 5. Definition of Done global (checklist por tarea)

- [ ] Compila e importa sin errores.
- [ ] Corre en al menos un mapa de prueba.
- [ ] Tests nuevos verdes + los viejos siguen verdes.
- [ ] `make lint` limpio (flake8 + mypy).
- [ ] Docstrings en lo público.
- [ ] Commit(s) atómicos con Conventional Commits.
- [ ] (Si toca un invariante) test del invariante actualizado.

---

## 6. Decisiones pendientes (a resolver mientras esbozamos)

> Estas 4 se **van cerrando sobre la marcha**. Cada una **bloquea** ciertas tareas: no se cierra
> una tarea marcada con ⏳ hasta que su decisión esté resuelta. Estado inicial: todas 🔴 abiertas.

| ID | Pregunta | Opciones | Bloquea | Decidir antes de | Estado |
|---|---|---|---|---|---|
| **D1** | Token de conexión en tránsito | (a) `D<id>-<origen>-<destino>` (dirección de viaje) · (b) otro formato | F4.1, F4.2, F7.2 | Día 3 | ✅ **cerrada (a)** |
| **D2** | ¿`cap(e)` se consume durante el tránsito? | (a) sí, la conexión queda ocupada durante el tránsito · (b) no | F3.3, F6.1, F6.2 | Día 3 | ✅ **cerrada (a)** |
| **D2b** | Duración de esa ocupación | (a) todo el tránsito (2 turnos, Ariel) · (b) solo el despegue (1 turno, Jose) | F3.3, F6.2 | Día 3 | 🟡 **recomendada (a)** + flag |
| **D3** | ¿Existen los mapas `.txt`? | (a) los provee el usuario · (b) reconstruir de figuras + repos | F1.2, F8.1 | Día 4 | ✅ **cerrada (a) — los provee el usuario** |
| **D4** | Prioridad de objetivos | (a) cerrar mandatory y después bonus · (b) apuntar al challenger temprano | F5, F9 | Día 11 | ✅ **cerrada (a) — mandatory primero** |
| **D5** | Prefijo de número de turno en la salida | (a) **sin** prefijo (subject §VII.5) · (b) con prefijo `turn N:` | F4.1 | Día 3 | ✅ **cerrada (a)** |

### 6.1 Contexto y recomendación de cada una

**D1 — Token de conexión en tránsito  ✅ CERRADA (a)**
- **Texto del subject (§VII.5):** *"Each movement must follow the format: `D<ID>-<zone>`, or
  `D<ID>-<connection>` in case of drones still in flight toward restricted zones. … `<connection>`
  is the name of the connection toward a restricted zone."* La conexión no tiene nombre propio: se
  define como `connection: <name1>-<name2>`, así que "su nombre" ES el par de zonas.
- **Decisión:** **(a)** — token `D<id>-<origen>-<destino>` en **dirección de viaje** (origen = dónde
  está el drone, destino = la zona restricted a la que va), con los **strings exactos** del input.
- **Evidencia (4/4 repos):** Jose `D<ID>-<from>-<to>` (`simulator.py`); Mario
  `f"D{id}-{origin}-{destination}"` (`formatting.py`); Ariel `D<id>-{connection.name}` con
  `name = "a-b"` (`formatter.py`, `connection.py`); Noel `D<id>-actual-next` (`simulation.py`).
  Orden de viaje, **no** orden de declaración: el validator de Jose exige `origin == posición actual`.
- **Impacto si se equivoca:** el evaluador parsea la salida → falla directa.

**D2 — Capacidad de la conexión durante el tránsito  ✅ CERRADA (a)**
- **Texto del subject (§VII.3):** *"the drone occupies the connection during transit"* y (§VII.2)
  *"Connection capacity limits how many drones can traverse the same connection simultaneously."*
  Ocupar = contar contra `max_link_capacity`.
- **Decisión:** **(a) estricta** — el tránsito hacia restricted **sí consume `cap(e)`**. Aislar el
  consumo tras un flag para poder cambiar la política sin tocar el simulador.
- **Evidencia:** Los dos repos de referencia consumen capacidad (Jose y Ariel). Coinciden en el
  Y/N; difieren en la duración (ver D2b).

**D2b — Duración de la ocupación  🟡 RECOMENDADA (a) + flag**
- **El subject es ambiguo:** "occupies the connection **during transit**" no dice si el tránsito es
  1 turno (solo despegue) o 2 (todo el vuelo).
- **Jose (1 turno):** `_apply_takeoff` mete el link; `_apply_arrival` devuelve `None` ("the transit
  meters the link only now, not on the landing turn"). Pipelining agresivo.
- **Ariel (2 turnos):** `reserve_move` reserva `range(turn, turn+cost)` → slots T y T+1; la zona
  destino recién en T+2. Token de conexión solo en la 1.ª línea, zona en la llegada (mismo output
  que Jose → **las 2 líneas de salida son idénticas**; la diferencia es solo la reserva interna).
- **Recomendación:** default **(a) todo el tránsito**. Es el literal ("during transit") y es
  **seguro bajo ambas lecturas**: reservar de más nunca excede capacidad (a lo sumo cuesta algún
  turno de pipelining). Correctitud > optimalidad. Igual, dejar la duración como **política detrás
  de un flag** (`transit_occupies_full_period: bool`) para poder medir el impacto en makespan.
- **Impacto si se equivoca:** schedules inválidos (si se reserva de menos) o makespan levemente peor
  (si se reserva de más).

**D3 — Mapas `.txt`  ✅ CERRADA (a)**
- **Evidencia:** el PDF **no adjunta** los mapas (solo figuras VII.1–VII.3).
- **Decisión:** **(a)** — **los provee el usuario.** No hace falta reconstruirlos. Igual conviene
  tener a mano mapas propios mínimos para los tests de invariantes (restricted, swap, capacidades).
- **Impacto si se equivoca:** no hay con qué benchmarkear → por eso la decisión desbloquea F1.2 y F8.1.

**D4 — Prioridad mandatory vs challenger  ✅ CERRADA (a)**
- **Evidencia:** E2 cierra mandatory con margen; el challenger es bonus (E4).
- **Decisión:** **(a)** — **cerrar mandatory primero**; el challenger solo tras el Hito M3.
- **Impacto:** define cuándo (y si) entramos a E4 (Space-Time A\*) en F9.

**D5 — Prefijo de número de turno en la salida  ✅ CERRADA (a)**
- **Texto del subject (§VII.5):** *"Each simulation turn is represented by a line. A line must list
  all the drone movements that occur during that turn, space-separated."* El **ejemplo** muestra
  **solo movimientos**, sin prefijo:
  ```
  D1-roof1 D2-corridorA
  D1-roof2 D2-tunnelB
  D1-goal D2-goal
  ```
- **Decisión:** **(a) sin prefijo** — una línea por turno con solo los movimientos. Los drones que
  esperan se omiten. Cuando todos llegaron, termina. **No existen "tokens de ocupación"** en el
  subject: los únicos tokens son `D<id>-<zona>` y `D<id>-<origen>-<destino>`.
- **Evidencia:** 4/4 repos emiten solo movimientos, sin número de turno (Jose `" ".join(tokens)`;
  Mario/Ariel/Noel igual). Jose además corta el loop si un turno no produce ningún token (deadlock)
  → nunca imprime líneas vacías ni entra en loop infinito.
- **Nota (sub-caso):** un turno sin ningún movimiento = deadlock → se corta (no se emite línea
  vacía). Un turno con *algunos* drones moviéndose y otros esperando → línea con los que se mueven.
- **Impacto si se equivoca:** si el evaluador espera solo movimientos y emitimos `turn N:`, el parseo
  falla igual que con D1.

### 6.2 Cómo las resolvemos

Para cada una: **(1)** releer el pasaje exacto del subject (`Fly-in Subjct.md`),
**(2)** contrastar con el consenso de los 4 repos, **(3)** si queda duda, **micro-experimento**
(mapita mínimo) y decidir. La decisión se registra acá (cambiar 🔴 → ✅) y, si toca el diseño, se
actualiza `plan_estructuracion_E2.md`.

> **Próximo paso:** ✅ **D1–D5 TODAS CERRADAS** contra el texto del subject + los 4 repos. No queda
> ninguna decisión bloqueante; solo la observación viva de **D2b** (duración de la ocupación, con
> default + flag). El siguiente paso real es el **esqueleto de repo** (F0.2–F0.5). Todo quedó
> reflejado en `spec_E2.md`.
