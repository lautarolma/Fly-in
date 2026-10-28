# Fly-in — Especificación (SDD) · Estrategia E2

> **Documento VIVO.** Se revisa y ajusta durante la implementación. Versión inicial: `v0.1`.
>
> **Proyecto:** Fly-in (42) · **Encuadre:** E2 — *k-caminos + asignación + scheduler validado*.
> **Versión del spec:** `v0.1` · **Fecha:** `2026-10-10` · **Estado:** en evolución.
>
> **Rol de este documento:** describe el **QUÉ** observable y testeable de cada componente
> (requisitos + escenarios). El **CÓMO** vive en `plan_estructuracion_E2.md`; el orden de ejecución
> en `plan_implementacion_E2.md`. Las decisiones se referencian por ID (**D1–D5**, ver
> `plan_implementacion_E2.md` §6): **D1, D2/D2b, D3, D4 y D5 están cerradas** (reflejadas acá). La
> única observación viva es la **duración exacta** de la ocupación de conexión (**D2b**), con default
> seguro (todo el tránsito) y flag para medir.
>
> **Fuente de verdad:** `Subjects/Fly-in/Fly-in Subjct.md` (v1.6). Ante cualquier divergencia entre
> este spec y el subject, **manda el subject**.

---

## 0. Convenciones

- **Lenguaje normativo:** **DEBE** (obligatorio), **DEBERÍA** (recomendado), **PUEDE** (opcional).
- **Escenarios:** formato **DADO / CUANDO / ENTONCES** (Given/When/Then).
- **Estado delta:** todo requisito es `[ADDED]` (no existe comportamiento previo).
- **Checks nombrados:** cada escenario apunta a un check futuro concreto (test `pytest` o
  `Validator.check_*`). El `Validator` es un componente **independiente** que re-deriva las reglas
  desde cero (no comparte lógica con el simulador).
- **Tipos de zona:** `normal`, `priority`, `restricted`, `blocked`.

### Dos superficies de validación (NO confundir)

| Superficie | Cuándo | Módulo | Nombres de check |
|---|---|---|---|
| **Validación de ENTRADA** | durante el parseo, antes de simular | `parsing` / `domain` | `input.check_*` |
| **Auditoría de SCHEDULE** | después de simular, sobre la salida | `validation` (juez **independiente**) | `validator.check_*` |

> El `Validator` (§REQ del juez) **re-deriva las reglas desde cero** y **no comparte lógica** con el
> simulador. La validación de entrada es otra cosa: vive en el parser, aborta con **línea + causa**,
> y **NO** es el juez de schedule. Mezclar ambas rompe SRP y la independencia del juez.

---

## REQ-PARSE-1: Parseo del mapa  `[ADDED]`

El sistema **DEBE** transformar el contenido de un archivo de mapa (texto) en objetos de dominio,
respetando la sintaxis de `Fly-in Subjct.md` §VI y §VII.4. El parseo **NO DEBE** depender de la capa
de presentación ni de la simulación.

#### Escenario: Parseo de un mapa válido
- **DADO** un archivo con `nb_drones: 5`, un `start_hub`, un `end_hub`, hubs y conexiones bien formados.
- **CUANDO** se invoca el parser sobre el archivo.
- **ENTONCES** devuelve un grafo con los drones, zonas y conexiones declarados, sin errores.
- **Check:** `test_parse_valid_map`.

#### Escenario: Primera línea con el número de drones
- **DADO** un archivo cuya primera línea es `nb_drones: <entero_positivo>`.
- **CUANDO** se parsea.
- **ENTONCES** el número de drones queda fijado a ese entero y cada drone recibe un ID único `D<i>`.
- **Check:** `test_parse_nb_drones`.

#### Escenario: Comentarios ignorados
- **DADO** un archivo con líneas que comienzan con `#`.
- **CUANDO** se parsea.
- **ENTONCES** esas líneas son ignoradas y no afectan el grafo resultante.
- **Check:** `test_parse_comments_ignored`.

#### Escenario: Metadatos en cualquier orden
- **DADO** una zona con `[zone=priority color=green max_drones=2]` en distinto orden de tags.
- **CUANDO** se parsea.
- **ENTONCES** cada tag se interpreta por nombre y los valores por defecto aplican a los ausentes.
- **Check:** `test_parse_metadata_any_order`.

---

## REQ-VALID-1: Validación de la estructura de entrada  `[ADDED]`

El sistema **DEBE** validar la entrada y **DEBE** detener la ejecución con un mensaje de error claro
que indique **la línea y la causa** ante cualquier violación. Los chequeos cubren: exactamente un
`start_hub` y un `end_hub`, nombres de zona únicos **y sin guiones ni espacios**, tipos de zona
válidos, capacidades enteras positivas, conexiones sólo entre zonas ya definidas y sin duplicados, y
poda de `blocked`. Estos chequeos pertenecen a la **validación de ENTRADA** (`input.check_*`, ver
§0), **no** al `Validator` de schedule.

#### Escenario: Un único start y un único end
- **DADO** un mapa con más de un `start_hub` o más de un `end_hub`.
- **CUANDO** se valida.
- **ENTONCES** el sistema aborta con un error que indica línea y causa.
- **Check:** `input.check_single_start_end`.

#### Escenario: Nombres de zona duplicados
- **DADO** dos zonas con el mismo nombre.
- **CUANDO** se valida.
- **ENTONCES** el sistema aborta con un error que indica línea y causa.
- **Check:** `input.check_unique_zone_names` / `test_duplicate_zone_name`.

#### Escenario: Nombre de zona con guion o espacio
- **DADO** una zona llamada `a-b` o `roof 1` (guion o espacio en el nombre).
- **CUANDO** se valida.
- **ENTONCES** el sistema aborta con un error de parsing que indica línea y causa.
- **Check:** `input.check_zone_name_chars` / `test_zone_name_no_dash_or_space`.

#### Escenario: Tipo de zona inválido
- **DADO** una zona con `zone=<tipo>` distinto de `normal|priority|restricted|blocked`.
- **CUANDO** se valida.
- **ENTONCES** el sistema aborta con un error de parsing que indica línea y causa.
- **Check:** `input.check_zone_types` / `test_invalid_zone_type`.

#### Escenario: Capacidad no positiva
- **DADO** una zona o conexión con `max_drones=0`, `max_drones=-1` o `max_link_capacity=0`.
- **CUANDO** se valida.
- **ENTONCES** el sistema aborta con un error que indica línea y causa.
- **Check:** `input.check_positive_capacities` / `test_nonpositive_capacity`.

#### Escenario: Conexión a zona inexistente o duplicada
- **DADO** una conexión que referencia una zona no definida, o una repetida (`a-b` y `b-a`).
- **CUANDO** se valida.
- **ENTONCES** el sistema aborta con un error que indica línea y causa.
- **Check:** `input.check_connection_refs` / `input.check_no_duplicate_connections`.

#### Escenario: Poda de zonas bloqueadas
- **DADO** un mapa con zonas `zone=blocked`.
- **CUANDO** se construye el grafo.
- **ENTONCES** las zonas `blocked` y sus conexiones incidentes quedan fuera del grafo navegable.
- **Check:** `input.check_blocked_pruned` / `test_blocked_pruned`.

---

## REQ-REACH-1: Alcanzabilidad del end  `[ADDED]`

El sistema **DEBE** verificar que exista al menos un camino del `start_hub` al `end_hub` que no use
zonas `blocked`. Si el `end_hub` no es alcanzable, **DEBE** abortar con un error claro y **NO DEBE**
entrar en un loop infinito.

#### Escenario: End alcanzable
- **DADO** un mapa conexo entre start y end.
- **CUANDO** se ejecuta el chequeo de alcanzabilidad.
- **ENTONCES** el chequeo pasa y la simulación puede iniciar.
- **Check:** `input.check_reachability`.

#### Escenario: End aislado por blocked
- **DADO** un mapa donde todo camino al `end_hub` pasa por una zona `blocked`.
- **CUANDO** se ejecuta el chequeo.
- **ENTONCES** el sistema aborta con un error claro y termina (sin loop infinito).
- **Check:** `input.check_reachability` / `test_unreachable_end_errors`.

---

## REQ-ZONE-1: Modelo de zona y costos de turno  `[ADDED]`

El sistema **DEBE** modelar cada zona con nombre, coordenadas enteras, tipo, capacidad y color. El
costo de entrar a una zona **DEBE** depender del **tipo de la zona DESTINO**: `normal` = 1 turno,
`priority` = 1 turno, `restricted` = 2 turnos, `blocked` = impasable (∞). `priority` es un
**desempate** en el pathfinding, **NO** un costo cero.

#### Escenario: Costo según el tipo de destino
- **DADO** un movimiento hacia una zona `normal`, `priority` o `restricted`.
- **CUANDO** se calcula su costo.
- **ENTONCES** el costo es 1, 1 y 2 turnos respectivamente.
- **Check:** `test_zone_turn_cost` / `validator.check_turn_cost`.

#### Escenario: Priority no es peso cero
- **DADO** dos caminos de igual costo, uno que pasa por `priority` y otro por `normal`.
- **CUANDO** el pathfinder desempata.
- **ENTONCES** se prefiere el que pasa por `priority` y ambos siguen costando 1 por zona.
- **Check:** `test_priority_tiebreak_cost_one`.

#### Escenario: Zona blocked impasable
- **DADO** una zona `blocked`.
- **CUANDO** el pathfinder evalúa entrar a ella.
- **ENTONCES** el movimiento es descartado (costo infinito).
- **Check:** `validator.check_blocked_impassable`.

---

## REQ-CONN-1: Modelo de conexión y capacidad  `[ADDED]`

El sistema **DEBE** modelar cada conexión como una arista **bidireccional** entre dos zonas, con
capacidad `max_link_capacity` (default 1). La clave canónica de una conexión **DEBE** ser
`tuple(sorted((a, b)))` para tratar `a-b` y `b-a` como la misma conexión. El grafo **DEBE** exponer
las zonas vecinas y la conexión entre dos zonas.

#### Escenario: Conexión bidireccional con clave canónica
- **DADO** una conexión `connection: a-b` y otra `connection: b-a`.
- **CUANDO** se indexan.
- **ENTONCES** ambas resuelven a la **misma** conexión y la segunda se marca duplicada.
- **Check:** `test_canonical_connection_key`.

#### Escenario: Capacidad por defecto
- **DADO** una conexión sin `max_link_capacity`.
- **CUANDO** se construye.
- **ENTONCES** su capacidad es 1.
- **Check:** `test_connection_default_capacity`.

---

## REQ-SIM-1: Simulación por turnos discretos (3 fases)  `[ADDED]`

El sistema **DEBE** simular en **turnos discretos**. En cada turno, **todos** los drones deciden y se
mueven **simultáneamente**. Cada turno **DEBE** ejecutarse en 3 fases: **decidir** (intenciones de
cada drone), **aplicar** (resolver capacidad/transit) y **commit** (fijar el estado nuevo de forma
atómica). Un drone **PUEDE** esperar (quedarse en su zona).

#### Escenario: Movimiento simultáneo
- **DADO** dos drones con movimientos compatibles en un mismo turno.
- **CUANDO** se resuelve el turno.
- **ENTONCES** ambos se mueven en el mismo turno (no en turnos consecutivos).
- **Check:** `test_simultaneous_move` / `validator.check_phase_commit`.

#### Escenario: Espera explícita
- **DADO** un drone sin movimiento válido disponible.
- **CUANDO** se resuelve el turno.
- **ENTONCES** el drone permanece en su zona y se omite de la línea del turno.
- **Check:** `test_wait_keeps_position`.

#### Escenario: Commit atómico
- **DADO** un turno con varias intenciones resueltas.
- **CUANDO** se aplica el commit.
- **ENTONCES** ninguna decisión ve un estado a medio actualizar (estado anterior o nuevo, nunca mixto).
- **Check:** `validator.check_phase_commit`.

---

## REQ-CAP-1: Enforcement de capacidades por turno  `[ADDED]`

En cada turno, el sistema **DEBE** garantizar que ninguna zona exceda su `max_drones` (default 1) ni
ninguna conexión su `max_link_capacity`. Las zonas `start_hub` y `end_hub` **NO DEBEN** tener límite
de capacidad (los drones pueden compartirlas libremente).

#### Escenario: Capacidad de zona respetada
- **DADO** una zona con `max_drones=1` ya ocupada y un drone que intenta entrar.
- **CUANDO** se resuelve el turno.
- **ENTONCES** el drone no entra (su movimiento se rechaza o espera).
- **Check:** `validator.check_zone_capacity`.

#### Escenario: Capacidad de conexión respetada
- **DADO** una conexión con `max_link_capacity=1` y dos drones que quieren usarla en el mismo turno.
- **CUANDO** se resuelve el turno.
- **ENTONCES** sólo un drone la usa en ese turno.
- **Check:** `validator.check_link_capacity_per_turn`.

#### Escenario: Start y end sin límite
- **DADO** N drones en el `start_hub` y varios llegando al `end_hub` en el mismo turno.
- **CUANDO** se resuelve.
- **ENTONCES** no se aplica límite de capacidad a ninguna de las dos zonas.
- **Check:** `validator.check_start_end_uncapped`.

---

## REQ-SWAP-1: La salida libera capacidad en el mismo turno  `[ADDED]`

El sistema **DEBE** evaluar la capacidad de una zona **después** de computar las salidas del mismo
turno. Un drone que sale de una zona libera su lugar **ese mismo turno**, de modo que un intercambio
(swap) entre dos drones en un mismo turno es válido si las capacidades lo permiten.

#### Escenario: Swap entre dos drones en un turno
- **DADO** dos zonas adyacentes `A` y `B` con `max_drones=1`, cada una con un drone, y ambos quieren intercambiarse.
- **CUANDO** se resuelve el turno.
- **ENTONCES** el intercambio se permite (ambos drones terminan en la zona del otro en un solo turno).
- **Check:** `test_swap_allowed` / `validator.check_leaver_frees_capacity`.

#### Escenario: Sin liberación, no hay cupo
- **DADO** una zona con `max_drones=1` ocupada por un drone que **no** sale, y otro que quiere entrar.
- **CUANDO** se resuelve el turno.
- **ENTONCES** el segundo drone no entra (no hay cupo real).
- **Check:** `validator.check_leaver_frees_capacity`.

---

## REQ-TRANSIT-1: Tránsito restringido  `[ADDED]`

Al moverse hacia una zona `restricted`, el drone **DEBE** ocupar la conexión durante el tránsito
(estado "en tránsito", turno de despegue) y **DEBE** entrar a la zona destino al turno siguiente
(llegada forzada). El drone **NO PUEDE** esperar sobre la conexión ni demorar la llegada. Ocupar la
conexión **DEBE** consumir `max_link_capacity`.

> **DECISIONES CERRADAS — D2 y D2b (`plan_implementacion_E2.md` §6).**
> - **D2 = (a):** el tránsito **sí consume `cap(e)`** (subject: "occupies the connection during transit").
> - **D2b = (a) default:** la ocupación dura **todo el tránsito** (2 turnos para restricted). Es el
>   literal del subject y es **seguro bajo ambas lecturas** (reservar de más nunca excede capacidad).
>   La duración **DEBE** quedar tras un flag (`transit_occupies_full_period`) para poder medir el
>   impacto en makespan contra la variante de Jose (1 turno, solo despegue).

#### Escenario: Tránsito ocupa la conexión un turno
- **DADO** un drone que se mueve hacia una zona `restricted`.
- **CUANDO** se resuelve el turno de partida.
- **ENTONCES** el drone queda "en tránsito" sobre la conexión y NO en la zona destino.
- **Check:** `test_restricted_transit_two_turns` / `validator.check_restricted_transit`.

#### Escenario: Llegada forzada al turno siguiente
- **DADO** un drone en tránsito hacia una zona `restricted`.
- **CUANDO** se resuelve el turno siguiente.
- **ENTONCES** el drone entra obligatoriamente a la zona destino, sin opción de esperar en la conexión.
- **Check:** `validator.check_restricted_transit`.

#### Escenario: El tránsito consume capacidad de conexión (D2)
- **DADO** una conexión con `cap(e)=1` usada por un drone en tránsito.
- **CUANDO** otro drone quiere usar la misma conexión ese turno.
- **ENTONCES** queda bloqueado (la conexión ya está ocupada por el drone en tránsito).
- **Check:** `test_transit_capacity` / `validator.check_link_capacity_per_turn`.

#### Escenario: La ocupación cubre todo el tránsito (D2b, default)
- **DADO** `transit_occupies_full_period = True` (default) y un drone en tránsito (2 turnos).
- **CUANDO** otro drone quiere usar la conexión en cualquiera de los dos turnos del tránsito.
- **ENTONCES** queda bloqueado en ambos turnos.
- **Check:** `test_transit_full_period_blocks_both_turns` (parametrizado por el flag D2b).

---

## REQ-OUT-1: Formato de salida por turno  `[ADDED]`

El sistema **DEBE** emitir la simulación como **una línea por turno**, **sin prefijo de número de
turno**, con los movimientos separados por espacio en el formato `D<ID>-<zona>` (o el token de
conexión de REQ-OUT-2). Los drones que no se mueven **DEBEN** omitirse de la línea. Los drones que
llegan al `end_hub` se consideran entregados y **NO DEBEN** volver a emitirse. Un turno en el que
**ningún** drone se mueve indica deadlock: el sistema **DEBE** terminar de forma controlada (sin
emitir una línea vacía y sin loop infinito). La simulación termina cuando todos los drones llegaron.

> **DECISIÓN CERRADA — D5 (`plan_implementacion_E2.md` §6) = (a) SIN prefijo de número de turno.**
> El subject (§VII.5 + ejemplo) muestra líneas de **solo movimientos**. Los "domain facts" que
> mencionaban prefijo de turno y tokens de ocupación **no existen** en el subject: los únicos tokens
> son `D<id>-<zona>` y `D<id>-<origen>-<destino>`. 4/4 repos coinciden.

#### Escenario: Una línea por turno con movimientos
- **DADO** un turno donde los drones D1 y D2 se mueven a `roof1` y `corridorA`.
- **CUANDO** se formatea la salida.
- **ENTONCES** la línea es `D1-roof1 D2-corridorA`, **sin** prefijo de número de turno.
- **Check:** `test_output_format_per_turn` / `validator.check_output_coherence`.

#### Escenario: La línea no lleva prefijo de turno
- **DADO** cualquier turno de la simulación.
- **CUANDO** se formatea la línea.
- **ENTONCES** la línea empieza con el token de un drone (`D...`), nunca con un número o `turn N:`.
- **Check:** `test_output_no_turn_prefix`.

#### Escenario: Drones quietos omitidos
- **DADO** un drone que espera en un turno.
- **CUANDO** se formatea la línea.
- **ENTONCES** ese drone no aparece en la línea.
- **Check:** `test_output_omits_waiting`.

#### Escenario: Turno sin movimientos corta la simulación
- **DADO** un turno en el que ningún drone puede moverse (deadlock).
- **CUANDO** se resuelve el turno.
- **ENTONCES** el sistema no emite una línea y termina de forma controlada (nunca loop infinito).
- **Check:** `test_no_infinite_loop` / `validator.check_deadlock`.

#### Escenario: Drones entregados no se re-emiten
- **DADO** un drone que ya llegó al `end_hub`.
- **CUANDO** avanzan los turnos siguientes.
- **ENTONCES** ese drone no vuelve a aparecer y la simulación termina cuando todos llegaron.
- **Check:** `validator.check_output_coherence` / `test_simulation_ends_when_all_delivered`.

---

## REQ-OUT-2: Token de conexión en tránsito  `[ADDED]`

Un drone en tránsito hacia una zona `restricted` **DEBE** emitirse, en el turno de despegue, con el
token `D<id>-<origen>-<destino>` — los **strings exactos del input**, en **dirección de viaje**
(origen = zona donde está el drone; destino = la zona `restricted` a la que vuela). En el turno
siguiente (llegada forzada) **DEBE** emitir `D<id>-<destino>`.

> **DECISIÓN CERRADA — D1 (`plan_implementacion_E2.md` §6) = (a) `D<id>-<origen>-<destino>`.**
> El subject (§VII.5) dice `D<ID>-<connection>` y la conexión se define como `a-b`; el nombre ES el
> par de zonas. Orden de **viaje**, no de declaración. 4/4 repos lo hacen así.

#### Escenario: Emisión del token de tránsito
- **DADO** un drone D1 en tránsito desde `roof1` hacia `tunnelB` (destino `restricted`).
- **CUANDO** se formatea el turno de despegue.
- **ENTONCES** el token es `D1-roof1-tunnelB`.
- **Check:** `test_output_connection_token`.

#### Escenario: Llegada con token de zona
- **DADO** el mismo drone D1 en tránsito hacia `tunnelB`.
- **CUANDO** se formatea el turno siguiente.
- **ENTONCES** el token es `D1-tunnelB` (llegada forzada).
- **Check:** `test_output_connection_token` / `validator.check_restricted_transit`.

---

## REQ-VIS-1: Representación visual (obligatorio)  `[ADDED]`

El subject (**Cap. VII.1**) **OBLIGA** a dar feedback visual de la simulación: salida de terminal
**coloreada** (estados de zonas + movimientos) **o** una interfaz gráfica. El sistema **DEBE**
ofrecer al menos una. La visualización **NO DEBE** contaminar la salida oficial (`REQ-OUT-1`), que
sigue siendo el contrato parseable por el evaluador.

> **Decisión de diseño:** el render coloreado se emite por un **canal/flujo separado** (p. ej.
> `stderr`) o detrás de un flag (`--visual`), de modo que **stdout** quede **byte a byte** con las
> líneas oficiales. Mezclar ANSI en las líneas de turno rompería el parseo del evaluador. `--visual`
> es opt-in; el render por defecto puede escribir a `stderr` sin alterar stdout.

#### Escenario: Render coloreado disponible
- **DADO** una ejecución de la simulación.
- **CUANDO** se activa la representación visual (o se corre con `--visual`).
- **ENTONCES** se muestran zonas y drones con colores por terminal, reflejando el estado por turno.
- **Check:** `test_render_colored_panel` / `renderer.render`.

#### Escenario: La salida oficial no se contamina
- **DADO** una ejecución con visualización activa.
- **CUANDO** se captura **stdout**.
- **ENTONCES** contiene **solo** las líneas oficiales `D<ID>-<zona>` (sin códigos ANSI ni texto extra).
- **Check:** `test_stdout_pure_official_lines`.

#### Escenario: Color inválido no rompe
- **DADO** una zona con `color=` no reconocido por el terminal.
- **CUANDO** se renderiza.
- **ENTONCES** se cae a un color por defecto, sin excepción.
- **Check:** `test_render_unknown_color_fallback`.

---

## REQ-CLI-1: Interfaz de línea de comandos  `[ADDED]`

El sistema **DEBE** exponerse como CLI usando `argparse`, recibiendo la **ruta del archivo de mapa**
como argumento. **DEBE** retornar códigos de salida coherentes: `0` en éxito y distinto de `0` ante
error (mapa inválido, `end` inalcanzable, argumentos inválidos).

#### Escenario: Ejecución con ruta válida
- **DADO** la invocación `python -m flyin <mapa.txt>` con un mapa válido.
- **CUANDO** corre.
- **ENTONCES** imprime la simulación y sale con código `0`.
- **Check:** `test_cli_valid_map_exit_0`.

#### Escenario: Ruta o argumentos inválidos
- **DADO** una invocación sin ruta o con un archivo inexistente.
- **CUANDO** corre.
- **ENTONCES** muestra un error claro y sale con código distinto de `0`.
- **Check:** `test_cli_bad_args_exit_nonzero`.

---

## REQ-BUILD-1: Contrato de build y tooling  `[ADDED]`

El proyecto **DEBE** incluir un `Makefile` con los targets **`install`**, **`run`**, **`debug`**,
**`clean`**, **`lint`** y **`lint-strict`**. `lint` **DEBE** correr `flake8 .` y `mypy .` con los
flags del subject; `lint-strict` **DEBE** correr `mypy --strict`. El proyecto **DEBE** incluir un
`.gitignore` (basura Python) y un `README.md` en **inglés** cuyo **primer renglón** sea la frase
itálica **exacta** exigida por el subject:

```
*This project has been created as part of the 42 curriculum by <login1>[, <login2>[, <login3>[...]]].*
```

El README **DEBE** además incluir al menos las secciones **Description**, **Instructions** y
**Resources** (con: descripción del algoritmo, representación visual, ejemplo de input/output, y uso
de IA).

#### Escenario: Targets del Makefile
- **DADO** el repositorio recién clonado.
- **CUANDO** se corren `make install`, `make run`, `make debug`, `make clean`, `make lint` y `make lint-strict`.
- **ENTONCES** cada target completa su tarea (lint y lint-strict sin errores).
- **Check:** `make_targets_smoke` (CI).

#### Escenario: Lint limpio
- **DADO** el código fuente.
- **CUANDO** se corre `make lint` y `make lint-strict`.
- **ENTONCES** no hay errores de `flake8` ni de `mypy`.
- **Check:** CI job `lint` + `lint-strict`.

#### Escenario: README en inglés
- **DADO** el archivo `README.md` en la raíz.
- **CUANDO** se inspecciona su primera línea.
- **ENTONCES** es la frase itálica **exacta** del subject y el documento está en inglés.
- **Check:** `test_readme_first_line` (manual/CI docs).

#### Escenario: README con secciones obligatorias
- **DADO** el `README.md`.
- **CUANDO** se inspeccionan sus encabezados.
- **ENTONCES** contiene al menos Description, Instructions y Resources.
- **Check:** `test_readme_sections` (manual/CI docs).

#### Escenario: .gitignore presente
- **DADO** el repositorio.
- **CUANDO** se lista la raíz.
- **ENTONCES** existe un `.gitignore` que excluye `__pycache__/`, `.venv/`, `.mypy_cache/`.
- **Check:** `test_gitignore_present` (CI/docs).

---

## REQ-ERR-1: Manejo de errores y robustez  `[ADDED]`

El sistema **NO DEBE** crashear por excepciones no capturadas durante el review, y **NO DEBE** entrar
en loops infinitos. Ante entrada inválida o estado irresoluble, **DEBE** emitir un mensaje claro y
terminar de forma controlada. Los recursos (archivos) **DEBEN** gestionarse con context managers.

#### Escenario: Mapa inválido no crashea
- **DADO** un mapa con un error de sintaxis o validación.
- **CUANDO** se ejecuta el programa.
- **ENTONCES** imprime un error con línea y causa y termina sin traceback no capturado.
- **Check:** `test_graceful_errors`.

#### Escenario: Sin loop infinito
- **DADO** un mapa con el `end_hub` inalcanzable o un deadlock de scheduling.
- **CUANDO** se ejecuta.
- **ENTONCES** el programa termina en tiempo acotado (error o aborto controlado), nunca cuelga.
- **Check:** `test_no_infinite_loop` / `validator.check_deadlock`.

#### Escenario: Cierre de recursos
- **DADO** la lectura de un archivo de mapa.
- **CUANDO** termina el parseo (éxito o error).
- **ENTONCES** el handle del archivo queda cerrado (context manager).
- **Check:** `test_file_handle_closed`.

---

## REQ-BENCH-1: Mapas de benchmark  `[ADDED]`

El sistema **DEBE** poder medirse contra los mapas de benchmark (easy/medium/hard) provistos por el
usuario, con las metas de turnos de `Fly-in Subjct.md` §VII.7.

> **DECISIÓN CERRADA — D3 = (a):** los mapas `.txt` **los provee el usuario**. No se reconstruyen.
> Además conviene tener mapas propios mínimos para los tests de invariantes (restricted, swap,
> capacidades), pero no reemplazan a los oficiales.

#### Escenario: Benchmark sobre mapas provistos
- **DADO** los mapas de benchmark provistos por el usuario.
- **CUANDO** se corre la simulación y se cuentan los turnos.
- **ENTONCES** se registra el makespan de cada mapa en una tabla y se compara con las metas §VII.7.
- **Check:** `bench_collect_makespans`.

---

## REQ-PRIO-1: Priorización mandatory vs challenger  `[ADDED]`

El orden de ataque **DEBE** registrarse: cerrar primero los mapas **mandatory** y recién después
apuntar al **challenger** (bonus).

> **DECISIÓN CERRADA — D4 = (a):** **mandatory primero**; el challenger (E4, Space-Time A\*) solo tras
> el Hito M3, si sobra tiempo.

#### Escenario: Gate de prioridad
- **DADO** el Hito M3 (E2 core completo).
- **CUANDO** se decide si continuar a E4 (Space-Time A\*).
- **ENTONCES** la decisión es continuar al bonus solo si el mandatory está cerrado.
- **Check:** revisión de hito M3 (gate humano, no test automático).

---

## REQ-OBJ-1: Objetivo de minimización (makespan)  `[ADDED]`

El sistema **DEBE** mover todos los drones del `start_hub` al `end_hub` minimizando el **makespan**
(turnos hasta que llega el último drone). La correctitud (respetar todas las reglas y capacidades)
**DEBE** tener prioridad sobre la optimalidad.

#### Escenario: Todos los drones entregados
- **DADO** un mapa con N drones y un `end_hub` alcanzable.
- **CUANDO** termina la simulación.
- **ENTONCES** los N drones están en el `end_hub` y el schedule pasa el `Validator`.
- **Check:** `validator.check_all_delivered`.

#### Escenario: Makespan bien definido
- **DADO** una simulación completa con líneas por turno.
- **CUANDO** se cuenta la cantidad de turnos emitidos.
- **ENTONCES** el makespan coincide con el turno en que llegó el último drone.
- **Check:** `test_makespan_count` / `estimator.makespan_bound`.

---

## Tabla de trazabilidad (Requisito → Escenario → Check futuro)

| Requisito | Escenario | Check futuro (test / validator) |
|---|---|---|
| REQ-PARSE-1 | Parseo de un mapa válido | `test_parse_valid_map` |
| REQ-PARSE-1 | Primera línea con número de drones | `test_parse_nb_drones` |
| REQ-PARSE-1 | Comentarios ignorados | `test_parse_comments_ignored` |
| REQ-PARSE-1 | Metadatos en cualquier orden | `test_parse_metadata_any_order` |
| REQ-VALID-1 | Un único start/end | `input.check_single_start_end` |
| REQ-VALID-1 | Nombres duplicados | `input.check_unique_zone_names` |
| REQ-VALID-1 | Nombre con guion/espacio | `input.check_zone_name_chars` |
| REQ-VALID-1 | Tipo de zona inválido | `input.check_zone_types` |
| REQ-VALID-1 | Capacidad no positiva | `input.check_positive_capacities` |
| REQ-VALID-1 | Conexión inexistente/duplicada | `input.check_connection_refs`, `check_no_duplicate_connections` |
| REQ-VALID-1 | Poda de blocked | `input.check_blocked_pruned` |
| REQ-REACH-1 | End alcanzable | `input.check_reachability` |
| REQ-REACH-1 | End aislado → error | `test_unreachable_end_errors` |
| REQ-ZONE-1 | Costo por tipo de destino | `validator.check_turn_cost` |
| REQ-ZONE-1 | Priority no es peso cero | `test_priority_tiebreak_cost_one` |
| REQ-ZONE-1 | Blocked impasable | `validator.check_blocked_impassable` |
| REQ-CONN-1 | Clave canónica bidireccional | `test_canonical_connection_key` |
| REQ-CONN-1 | Capacidad por defecto | `test_connection_default_capacity` |
| REQ-SIM-1 | Movimiento simultáneo | `test_simultaneous_move` |
| REQ-SIM-1 | Espera explícita | `test_wait_keeps_position` |
| REQ-SIM-1 | Commit atómico | `validator.check_phase_commit` |
| REQ-CAP-1 | Capacidad de zona | `validator.check_zone_capacity` |
| REQ-CAP-1 | Capacidad de conexión | `validator.check_link_capacity_per_turn` |
| REQ-CAP-1 | Start/end sin límite | `validator.check_start_end_uncapped` |
| REQ-SWAP-1 | Swap en un turno | `test_swap_allowed` |
| REQ-SWAP-1 | Sin liberación no hay cupo | `validator.check_leaver_frees_capacity` |
| REQ-TRANSIT-1 **[D2]** | Ocupa la conexión un turno | `validator.check_restricted_transit` |
| REQ-TRANSIT-1 **[D2]** | Llegada forzada | `validator.check_restricted_transit` |
| REQ-TRANSIT-1 **[D2]** | Consume capacidad de conexión | `test_transit_capacity` |
| REQ-TRANSIT-1 **[D2b]** | Ocupación cubre todo el tránsito | `test_transit_full_period_blocks_both_turns` |
| REQ-OUT-1 | Una línea por turno | `validator.check_output_coherence` |
| REQ-OUT-1 **[D5]** | Sin prefijo de turno | `test_output_no_turn_prefix` |
| REQ-OUT-1 | Quietos omitidos | `test_output_omits_waiting` |
| REQ-OUT-1 | Turno sin movimientos corta | `test_no_infinite_loop` |
| REQ-OUT-1 | Entregados no re-emitidos | `validator.check_output_coherence` |
| REQ-OUT-2 **[D1]** | Token de tránsito | `test_output_connection_token` |
| REQ-VIS-1 | Render coloreado disponible | `test_render_colored_panel` |
| REQ-VIS-1 | stdout no contaminado | `test_stdout_pure_official_lines` |
| REQ-VIS-1 | Color inválido no rompe | `test_render_unknown_color_fallback` |
| REQ-CLI-1 | Ruta válida (exit 0) | `test_cli_valid_map_exit_0` |
| REQ-CLI-1 | Args inválidos (exit ≠ 0) | `test_cli_bad_args_exit_nonzero` |
| REQ-BUILD-1 | Targets del Makefile | `make_targets_smoke` |
| REQ-BUILD-1 | Lint limpio | CI `lint` + `lint-strict` |
| REQ-BUILD-1 | README en inglés | `test_readme_first_line` |
| REQ-BUILD-1 | Secciones del README | `test_readme_sections` |
| REQ-BUILD-1 | `.gitignore` presente | `test_gitignore_present` |
| REQ-ERR-1 | Mapa inválido no crashea | `test_graceful_errors` |
| REQ-ERR-1 | Sin loop infinito | `test_no_infinite_loop` |
| REQ-ERR-1 | Cierre de recursos | `test_file_handle_closed` |
| REQ-BENCH-1 | Benchmark de mapas | `bench_collect_makespans` |
| REQ-PRIO-1 | Gate de prioridad | revisión M3 |
| REQ-OBJ-1 | Todos entregados | `validator.check_all_delivered` |
| REQ-OBJ-1 | Makespan bien definido | `estimator.makespan_bound` |

---

## Decisiones referenciadas

| ID | Tema | Requisitos afectados | Estado |
|---|---|---|---|
| **D1** | Token de conexión en tránsito | REQ-OUT-2 | ✅ cerrada → `D<id>-<origen>-<destino>` (viaje) |
| **D2** | `cap(e)` durante el tránsito | REQ-TRANSIT-1 | ✅ cerrada → sí, consume capacidad |
| **D2b** | Duración de la ocupación | REQ-TRANSIT-1 | 🟡 default: todo el tránsito + flag |
| **D3** | Mapas `.txt` de benchmark | REQ-BENCH-1 | ✅ cerrada → los provee el usuario |
| **D4** | Prioridad mandatory vs challenger | REQ-PRIO-1 | ✅ cerrada → mandatory primero |
| **D5** | Prefijo de turno en la salida | REQ-OUT-1 | ✅ cerrada → sin prefijo |

> El cierre de D1, D2/D2b, D3, D4 y D5 quedó registrado en `plan_implementacion_E2.md` §6 (🔴 → ✅).
> Única observación abierta: la **duración exacta** de la ocupación de la conexión (D2b), con default
> seguro (todo el tránsito) y flag para medir.
