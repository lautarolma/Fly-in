# Fly-in — Cronograma de trabajo E2

> **Documento VIVO.** Se re-estima al cierre de cada semana y en cada checkpoint del
> `plan_implementacion_E2.md` §4. Versión inicial: `v0.1`.
>
> **Supuestos:** jornadas de **≥4h** (nominal 5h), **uso intensivo de agentes de IA**, y **tiempo de
> estudio teórico incluido** (entender algoritmos, no solo hacerlos andar).

---

## 0. Supuestos y definición de "jornada tipo"

- **Duración:** 4h mínimo, **5h nominal**. Los días "pesados" (invariantes, simulación) pueden
  estirarse a 5–6h; los livianos (docs, CI) bajan a 4h.
- **Jornada tipo (5h):**

| Bloque | Tiempo | Qué |
|---|---|---|
| Estudio / repaso del concepto del día | 45 min | leer/entender el algoritmo o el invariante **antes** de codear |
| Diseño + delegación a agente de IA | 30 min | definir la tarea, el contrato y los tests que debe cumplir |
| Revisión de código del agente | 45 min | **tú entendés línea por línea** lo que el agente escribió |
| Escritura/ajuste propio (lo crítico) | 1h 30min | invariantes, algoritmos, integración |
| Tests + lint + commit | 1h | correr verdes, `make lint`, commit convencional |
| Docs / notas del día | 30 min | actualizar el plan si cambió algo |

- **Regla de oro de la jornada:** no se cierra el día sin **tests verdes + `make lint` limpio +
  commit atómico**. Si no llegás, se cierra con un commit a medias **en branch** y se continúa al
  día siguiente (nunca `main` roto).

---

## 1. Resumen por fase

| Fase | Nombre | Horas estimadas | Días (≈5h) |
|---|---|---|---|
| **F0** | Setup, tooling y estudio | 10.5h | 2 |
| **F1** | Parser + Dominio | 10h | 2 |
| **F2** | PathFinder (Dijkstra/A\*) | 7.5h | 1.5 |
| **F3** | Simulador base (Propuesta A) | 11.5h | 2.5 |
| **F4** | Salida y Render | 5.5h | 1 |
| **F5** | K-caminos + Estimador | 11h | 2 |
| **F6** | Scheduler con reservas | 9h | 2 |
| **F7** | Validador independiente | 6.5h | 1.5 |
| **F8** | Hardening, benchmarks y defensa | 11.5h | 2 |
| | **Subtotal core (F0–F8)** | **≈83h** | **≈17 días** |
| **F9** | Bonus E4 (Space-Time A\*) | 13h | 2.5–3 |

> **Total core:** ~17 jornadas (~3.5 semanas). **Con bonus E4:** ~20 jornadas (~4 semanas).

---

## 2. Calendario día por día (core)

### Semana 1 — Fundamentos

| Día | Fase | Foco | Horas | Entregable al cerrar | Concepto a estudiar |
|---|---|---|---|---|---|
| **1** | F0.1–F0.2 | Estudio del modelo + esqueleto de repo | 5h | Notas de modelo + `uv sync` ok | turnos, capacidades, restricted, swap |
| **2** | F0.3–F0.6 | Makefile + lint/mypy + CI + convención git | 5h | `make lint` + CI verde en esqueleto | tipado, flake8, GitHub Actions |
| **3** | F1.1–F1.2 | Modelo de dominio + Parser | 5h | Parseo con errores claros | `dataclass(frozen)`, Enum, errores con contexto |
| **4** | F1.3–F1.5 | Validación + alcanzabilidad + Graph | 5h | Grafo + validación completa | BFS de alcanzabilidad |
| **5** | F2.1–F2.2 | Interfaz PathFinder + Dijkstra | 4h | Dijkstra correcto con pesos de vértice | cola de prioridad (`heapq`), Dijkstra |

**Hito M1 (fin Día 5):** tooling, modelo y pathfinder listos. `make lint-strict` + CI verdes.

### Semana 2 — El corazón

| Día | Fase | Foco | Horas | Entregable al cerrar | Concepto a estudiar |
|---|---|---|---|---|---|
| **6** | F2.3–F2.4 | Dijkstra reverso + A\* | 4h | `dist_to_end` + A\* | heurística admisible/consistente |
| **7** | F3.1–F3.2 | Drone FSM + loop de 3 fases | 5h | Simulador avanzando turnos | máquina de estados, commit simultáneo |
| **8** | F3.3–F3.4 | **Transit restricted + Swap** | 5h | Invariantes #1 y #2 con test | in-transit, liberar-antes-de-validar |
| **9** | F3.5–F3.6, F4.1 | Capacidades + asignación simple + formateador | 5h | Líneas de turno correctas | capacidades por turno, formato de salida |
| **10** | F4.2–F4.4 | Token de tránsito + render + errores | 4h | Salida `easy` byte a byte | formato exacto, ANSI colors |

**Hito M2 (fin Día 10):** **Propuesta A corre y pasa `easy` byte a byte.** (Ya "aprobás" en chico.)

### Semana 3 — El salto a E2

| Día | Fase | Foco | Horas | Entregable al cerrar | Concepto a estudiar |
|---|---|---|---|---|---|
| **11** | F5.1–F5.2 | k-caminos (node-disjoint/penalización) + cotas | 5h | k rutas candidatas | caminos disjuntos, penalización |
| **12** | F5.3–F5.5 | Estimador + selección + allocator | 5h | Reparto por rutas | cota de makespan (lem-in) |
| **13** | F6.1–F6.2 | Reservas + política de scheduler | 5h | Scheduler con reservas | scheduling con recursos |
| **14** | F6.3–F6.4 | Deadlock detection + reintentos | 5h | Schedules válidos solos | deadlock, retry |
| **15** | F7.1–F7.3 | **Validador independiente** + integración CI | 5h | Juez corriendo sobre todo | test de propiedad, independencia |

**Hito M3 (fin Día 15):** **E2 completo** — k-rutas + estimator + scheduler + validador. Mandatory
cerrados con margen. **Checkpoint de re-estimación #1** (¿alcanza para hard? ¿seguimos a E4?).

### Semana 4 — Cierre y decisión

| Día | Fase | Foco | Horas | Entregable al cerrar | Concepto a estudiar |
|---|---|---|---|---|---|
| **16** | F8.1–F8.2 | Benchmarks mandatory + tuning de hard | 5h | Tabla de makespans | profiling, tuning de k |
| **17** | F8.3–F8.5 | README (EN) + `mypy --strict` + ensayo defensa | 5h | Repo listo + guion | narrativa técnica, defensa |

**Hito M4 (fin Día 17):** **proyecto defendible.** M4 es el **GO/NO-GO del bonus E4**.

### Bonus (Días 18–20, si M4 dice GO)

| Día | Fase | Foco | Horas |
|---|---|---|---|
| **18** | F9.1–F9.2 | Estado `(zona,turno)` + reservation table | 5h |
| **19** | F9.3 | A\* espacio-temporal + ventana + límite seguridad | 5h |
| **20** | F9.4 | Replan + integración + medir challenger | 4h |

**Hito M5 (bonus):** challenger medido; ideal **< 45 turnos**.

---

## 3. Reparto de horas (core ≈83h)

| Actividad | % | Horas |
|---|---|---|
| Estudio / entender el concepto | ~18% | ~15h |
| Código | ~45% | ~37h |
| Tests + validación | ~22% | ~18h |
| Docs / README / defensa | ~10% | ~8h |
| Setup / CI / git | ~5% | ~5h |

> **Nota:** casi **1 de cada 4 horas se va en tests**. No es tiempo perdido: es lo que convierte
> "funciona en mi cabeza" en "aprueba en el evaluador".

---

## 4. Rol de los agentes de IA (por fase)

> **Principio:** *el agente ejecuta, yo dirijo.* Delegás lo mecánico; te quedás con lo que hay que
> **entender y defender**.

| Fase | Delegás a la IA | **NO** delegás (lo hacés/entendés vos) |
|---|---|---|
| F0 | Makefile, config de lint/mypy, YAML de CI | entender qué chequea cada tool |
| F1–F2 | boilerplate de dataclasses, parser, tests de borde | la lógica de Dijkstra y el tie-break |
| F3 | scaffolds del simulador, casos de test | **invariantes #1/#2 (transit/swap)** |
| F4 | formateador, colores | verificación byte a byte del formato |
| F5–F7 | generar candidatos de código, docs, refactors | diseño del estimator/scheduler/validador |
| F8 | README, docstrings, tabla de benchmarks | narrativa de defensa |
| F9 | scaffolds de espacio-tiempo | admisibilidad de la heurística |

**Formato de pedido al agente (una tarea por vez):** contexto (archivo/capas implicadas) +
contrato (firma/entrada/salida) + **tests que debe cumplir** + "explicá los trade-offs". Revisás
antes de commitear.

---

## 5. Hitos (milestones) y gates

| Hito | Cuándo | Criterio de éxito | Gate |
|---|---|---|---|
| **M1** | fin Día 5 | `make lint-strict` + CI verdes; pathfinder correcto | seguir |
| **M2** | fin Día 10 | Propuesta A pasa `easy` byte a byte | seguir |
| **M3** | fin Día 15 | E2 completo; mandatory con margen | **re-estimación #1** |
| **M4** | fin Día 17 | Repo defendible, README EN, ensayo hecho | **GO/NO-GO E4** |
| **M5** | Día 20 | Challenger validado | (bonus) |

---

## 6. Buffer y puntos de re-estimación

- **Buffer semanal:** el sábado (o el día 5/10/15) no se empieza tarea nueva; se **absorbe atraso**
  y se **re-estima** la semana siguiente.
- **Puntos de re-estimación formal:** fin de cada semana + Checkpoint #1 (fin F5).
- **Regla del buffer:** si una fase se atrasa >50%, se **recorta alcance** (ej.: A\* opcional,
  pygame opcional) antes que estirar la fecha.

---

## 7. Escenarios

| Escenario | Ritmo | Días core | Con nota |
|---|---|---|---|
| **Optimista** | 5h/día, agente muy ágil, sin imprevistos | **~13 días** | +3 E4 |
| **Realista** | 5h/día, con estudio y algún rework | **~17 días** | +3 E4 |
| **Con holgura** | 4h/día, días salteados, rework de invariantes | **~21 días** | E4 opcional |

> **Recomendación:** planificá **~3,5 semanas (17 jornadas)** para E2 core y dejá la **semana 4**
> para el bonus. Si terminás antes, ese tiempo es tu **colchón de defensa**.

---

## 8. Lo que hay que cerrar ANTES de arrancar el Día 1

> ✅ **TODAS LAS DECISIONES CERRADAS.** Ya no bloquean nada. Ver el registro completo en
> `plan_implementacion_E2.md` §6.

| # | Decisión | Estado |
|---|---|---|
| 1 | Token de conexión en tránsito → `D<id>-<origen>-<destino>` (D1) | ✅ cerrada |
| 2 | ¿`cap(e)` se consume durante el tránsito? → sí (D2); duración = todo el tránsito + flag (D2b) | ✅ cerrada (D2b 🟡 default + flag) |
| 3 | ¿Existen los mapas `.txt`? → los provee el usuario (D3) | ✅ cerrada |
| 4 | ¿Prioridad? → mandatory primero (D4) | ✅ cerrada |

> **Único pendiente real para arrancar:** el **esqueleto de repo** (`pyproject`, `Makefile`, CI).
> Con eso, Día 1 listo.
