# Fly-in — Comparativa de encuadres y estrategias (mirada de decisión + valor de mercado)

> **Objetivo:** decidir **cómo encarar Fly-in**. Contrasta **(a)** los 3 encuadres que propuse en
> `Subjects/Fly-in/propuestas_resolucion.md`, **(b)** 4 repositorios reales de la comunidad 42
> (Noel, Mario, Ariel, Jose) **clonados y leídos a nivel de código, configuración y `git`**, y
> **(c)** los repos de la investigación previa (`analisis.md`).
>
> **Tus criterios** (los que mandan):
> 1. **Aprender** cosas importantes para tu formación.
> 2. **Tecnología** — entendida en sentido amplio: **algoritmos, granularidad, escalabilidad y
>    todo valor añadido que el sector tech premia**.
> 3. **Implementación rápida.**
> 4. **Evitar complejidad conceptual** que se vuelva un dolor de cabeza.
> 5. **Defender el proyecto con total claridad.**
>
> Perfil de entrada: **a-maze-ing (BFS, DSU)**, **push_swap (K-sort)**, **call_me_maybe (Trie, FSM,
> schema-contexts)**.

---

## 0. Glosario

### Algoritmos y conceptos
| Sigla | Nombre completo | En qué consiste |
|---|---|---|
| **BFS** | Breadth-First Search (búsqueda en anchura) | Explora por niveles con una cola; camino más corto **solo si las aristas valen 1**. Ya lo usás en a-maze-ing. |
| **Dijkstra** | Algoritmo de Dijkstra | Camino más corto con **pesos no negativos** (cola de prioridad). |
| **A\*** | A-star | Dijkstra + heurística admisible `h`: `f = g + h`. Dirige la búsqueda a la meta. |
| **WHCA\*** | Windowed Hierarchical Cooperative A\* | A\* **espacio-temporal** (estado = zona+turno) contra una tabla de reservas, por ventanas. |
| **MAPF** | Multi-Agent Path Finding | Planificar rutas de **varios** agentes evitando colisiones. |
| **MCMF** | Min-Cost Max-Flow | Máximo flujo (drones) al mínimo costo. |
| **SSP** | Successive Shortest Paths | Método para MCMF: aumentar flujo por caminos mínimos. |
| **FSM** | Finite State Machine (máquina de estados) | Estados y transiciones; ya lo usás en call_me_maybe. |
| **makespan** | — | Turnos que tarda el **último** drone en entregar. La métrica a minimizar. |
| **node-disjoint** | — | Caminos que **no comparten nodos** entre sí. |

### Ingeniería y "valor de mercado"
| Sigla | Nombre completo | En qué consiste |
|---|---|---|
| **granularidad** | — | Qué tan finas/cohesivas son las unidades: commits, módulos/clases, tests. |
| **escalabilidad** | — | Cómo crece el costo (tiempo/memoria) cuando crecen los datos; y si el código admite crecer en features/equipo. |
| **LOC** | Lines of Code | Líneas de código. |
| **SoC** | Separation of Concerns (separación de incumbencias) | Cada parte hace una cosa; base de la granularidad. |
| **SRP** | Single Responsibility Principle | Cada clase/función tiene **una** razón para cambiar. |
| **DI** | Dependency Injection | Pasar dependencias desde afuera en vez de instanciarlas adentro (testeable). |
| **ABC** | Abstract Base Class | Clase abstracta en Python (`abc`); define una interfaz. |
| **Protocol** | (structural typing) | "Duck typing" tipado (`typing.Protocol`); contrato sin herencia. |
| **PR** | Pull Request | Propuesta de merge revisable en GitHub/GitLab. |
| **Conventional Commits** | — | Estándar de mensajes `feat:`, `fix:`, `chore:`… automatiza changelog/versionado. |
| **CI** | Continuous Integration | Automatización (acá **GitHub Actions**) que corre lint/test en cada push. |
| **uv** | (Astral) uv | Gestor de proyectos Python en **Rust**; reemplaza pip/venv/poetry. Estado del arte 2024+. |
| **pydantic** | — | Validación de datos por tipos (v2 con núcleo en Rust). |
| **FastAPI** | — | Framework web **asíncrono**. |
| **pyproject.toml** | (PEP 621/518) | Config estándar del proyecto Python. |
| **mypy / flake8** | — | Chequeo **estático de tipos** / **linter** de estilo. |
| **pytest** | — | Framework de testing estándar de facto. |
| **pygame-ce** | pygame Community Edition | Fork de pygame para **visualización**. |

---

## 1. Qué cuenta como "tecnología" en este documento

Tomo tu matiz al pie de la letra. "Tecnología" no es solo el lenguaje o el framework: es **todo
activo profesional** que suma. Lo divido en **3 capas**:

| Capa | Qué incluye | Por qué el sector lo premia |
|---|---|---|
| **① Algoritmos** | Dijkstra, A\*, heurísticas, cotas, scheduling, flujo, MAPF | Es la señal #1 en entrevistas técnicas y en problemas "duros" (ruteo, logística, planificación). |
| **② Ingeniería** | **granularidad** (módulos/commits/tests), **escalabilidad**, SRP/SoC, DI, tipado, testing, CI, tooling | Es lo que separa "código que anda" de "código que un equipo puede mantener". |
| **③ Cultura de trabajo** | `git` profesional (branches/PRs/conventional commits), trabajar con agentes de IA, docs | Es lo que te hace **empleable y productivo** desde el día 1. |

> **Frase para llevarte:** un proyecto puede ser **simple** (capa ①) y **excelente** (capas ② y ③).
> La dificultad de la capa ① **no** te da puntos extras por sí sola — y sí te puede hundir.

---

## 2. Las 6 lentes de comparación

| # | Lente | Pregunta |
|---|---|---|
| **L1** | **Velocidad de implementación** | ¿Cuánto tardás en tener algo que compila, corre y aprueba? |
| **L2** | **Baja complejidad conceptual** | ¿Cuánto "dolor de cabeza" te da entenderlo de verdad? |
| **L3** | **Defendibilidad** | ¿Podés explicarlo de punta a punta, sin agujeros? |
| **L4** | **Valor formativo** | ¿Qué conceptos sólidos te llevás? |
| **L5** | **Transferibilidad** | ¿Cuánto sirve HOY o en próximos proyectos? |
| **L6** | **Valor de mercado** | ¿Qué tan fuerte es la señal para un recruiter/entrevistador/equipo? |

---

## 3. La idea central

> ## ⚡ Tres perillas SEPARADAS: **algoritmo**, **ingeniería** y **cultura**.
> Podés tener un algoritmo **simple** (E1/E2) y a la vez ingeniería **de nivel mercado**
> (`uv`, `pyproject`, `mypy --strict`, `flake8`, `pytest`, CI) y cultura **profesional**
> (`git` con branches/PRs/conventional commits).
>
> El dolor de cabeza viene de la **capa ①** (MCMF, WHCA\*). Las capas ② y ③ son **baratas de
> aprender y muy rentables**. Elegí el algoritmo por **riesgo de aprobación** y las otras dos por
> **aprendizaje + mercado**.

**Evidencia:** Mario y Jose NO tienen algoritmos más "difíciles" (E1/E2) que Ariel (E4), pero
tienen **135 y 177 commits con PRs, CI y tipado estricto**. Ariel tiene el mejor algoritmo y **22
commits informales sin CI**. El mercado premia más el **conjunto** que el truco algorítmico suelto.

---

## 4. Taxonomía: las 4 familias de encuadre

| Enc. | Familia | Idea central | Repos |
|---|---|---|---|
| **E1** | **Camino único reactivo** | Un solo camino; el simulador espera/recalcula al congestionarse. | **Noel**, **Jose**. |
| **E2** | **K-caminos + asignación + scheduler validado** | Varios caminos candidatos, reparto de drones, scheduler con reservas. | **Mario**; base de `analisis.md`. |
| **E3** | **Encuadre de flujo** | Modelar como flujo (node-splitting) y resolver con MCMF; el flujo elige caminos. | Repos **lem-in**; casi nadie en Fly-in. |
| **E4** | **MAPF cooperativo espacio-temporal** | Planificación conjunta `(zona, turno)` con tabla de reservas. | **Ariel** (WHCA\*). |

> Los **mandatory los pasa hasta E1**. La diferencia se juega en makespan **multicamino** y challenger.

---

## 5. Detalle por encuadre (técnica + 6 lentes + granularidad + escalabilidad + valor del algoritmo)

### E1 — Camino único reactivo

- **Algoritmos:** Dijkstra/A\* para **un** camino; bucle de turnos con FSM por drone; replan opcional.
- **Granularidad:** gruesa. Pocas piezas (PathFinder + Simulador + Parser). Fácil de partir si querés.
- **Escalabilidad:** *regular*. El path escala bien; el **replan reactivo** puede degradar a
  `O(turnos × Dijkstra)`. Con muchas rutas alternativas, el embudo empeora el makespan.
- **Valor de mercado del algoritmo:** **básico**. Dijkstra es obligatorio saberlo, pero no diferencia.

| Lente | Pts | Comentario |
|---|---|---|
| L1 Velocidad | **5** | El más rápido: 3–4 días con todo. |
| L2 Baja complejidad | **5** | Cero teoría nueva. |
| L3 Defendibilidad | **5** | Lo explicás en 5 minutos. |
| L4 Valor formativo | **2** | Dijkstra + sim básica. |
| L5 Transferibilidad | **3** | Solo si le metés tooling a mano. |
| L6 Valor de mercado | **2** | Señal débil: "hizo lo mínimo". |

- **Tiempo:** núcleo **1–2 d** / completo **3–4 d**. **Riesgo aprobación:** ⚠️ medio (hard multicamino).

### E2 — K-caminos + asignación + scheduler validado  ⭐

- **Algoritmos:** A\*/Dijkstra **exacto** (heurística inversa admisible); **k caminos**
  (node-disjoint / penalización / Yen); **estimador de makespan** (`max(costo_i + carga_i − 1)` y
  por recurso `⌈carga/capacidad⌉ − 1 + costo`); asignación greedy/round-robin (ETA); **scheduler con
  reservas** + **validador independiente**.
- **Granularidad:** **fina y natural**. Se separa en PathFinder / RouteBuilder / Estimator /
  Allocator / Scheduler / Validator — cada uno testeable por su cuenta (SRP + DI reales).
- **Escalabilidad:** **buena**. Init `O(k·(V+E) log V)` + enumeración acotada de subconjuntos; sim
  `O(T·N·grado)`. Es el único que **controla la combinatoria** explícitamente (Mario: ≤4 rutas de 8).
- **Valor de mercado del algoritmo:** **alto**. Scheduling con recursos + heurísticas + cotas es
  ruteo/logística real (job-shop, bin-packing, planificación de flotas).

| Lente | Pts | Comentario |
|---|---|---|
| L1 Velocidad | **4** | 6–8 días; núcleo en 3–4. |
| L2 Baja complejidad | **3.5** | Más piezas, pero cada una simple. |
| L3 Defendibilidad | **4** | El validador te blinda en la defensa. |
| L4 Valor formativo | **5** | Grafos + scheduling + testing + cotas. |
| L5 Transferibilidad | **5** | Encaja perfecto con el stack moderno. |
| L6 Valor de mercado | **5** | Señal fuerte y moderna. |

- **Tiempo:** núcleo **3–4 d** / completo **6–8 d**. **Riesgo aprobación:** ✅ bajo (challenger 43).

### E3 — Encuadre de flujo (MCMF + node-splitting)

- **Algoritmos:** node-splitting (`v_in → v_out`); **MCMF** con SSP + potenciales de Johnson.
- **Granularidad:** fina en teoría, pero **acoplada** (el flujo es una sola máquina difícil de partir).
- **Escalabilidad:** `O(N·E log V)` para el flujo. Buena en teoría; en la práctica, difícil de debuggear.
- **Valor de mercado del algoritmo:** **alto pero de nicho**. Redes de flujo es clásico de
  competitive programming y logística; raro en entrevistas de producto.

| Lente | Pts | Comentario |
|---|---|---|
| L1 Velocidad | **2** | Estudio previo obligatorio. |
| L2 Baja complejidad | **1.5** | El mayor dolor de cabeza de los 4. |
| L3 Defendibilidad | **3** | Fuerte teórica, difícil de explicar el interior. |
| L4 Valor formativo | **5** | Flujo, dualidad, costos reducidos. |
| L5 Transferibilidad | **3.5** | Nicho para tu perfil. |
| L6 Valor de mercado | **4.5** | Impresiona, pero pocas ofertas lo piden. |

- **Tiempo:** núcleo **4–6 d** / completo **8–11 d**. **Riesgo:** bugs silenciosos.

### E4 — MAPF cooperativo espacio-temporal (WHCA\* / Space-Time A\*)  🏆

- **Algoritmos:** A\* espacial (heurística inversa); **A\* espacio-temporal** (`(zona, turno)`,
  esperar como arista); **tabla de reservas** `(zona,t)`/`(conexión,t)`; replan por ventana + holds.
- **Granularidad:** fina y elegante (Simulator con ABC/observer, ReservationTable genérica).
- **Escalabilidad:** **la mejor** por agente; `O(N·Z·W·grado·log(Z·W))` por ronda, replan cada `W/2`.
  En la práctica, 25 drones en **~0.25 s**.
- **Valor de mercado del algoritmo:** **muy alto y "senior"**. MAPF es investigación aplicada:
  robótica, almacenes (Amazon), videojuegos, ruteo. Diferenciador en una entrevista.

| Lente | Pts | Comentario |
|---|---|---|
| L1 Velocidad | **2.5** | Depende de tener A\* afinado antes. |
| L2 Baja complejidad | **2** | El más "fino"; bugs difíciles. |
| L3 Defendibilidad | **3** | Explicás el concepto, pero cada decisión cuesta. |
| L4 Valor formativo | **5** | Campo real de investigación. |
| L5 Transferibilidad | **4.5** | A\*/planificación se usan en robótica/juegos. |
| L6 Valor de mercado | **5** | Señal senior muy fuerte. |

- **Tiempo:** núcleo **5–7 d** / completo **9–14 d**. **Riesgo:** choques sutiles.

---

## 6. Los 4 repos: stack, granularidad y señales de mercado

### 6.1 Stack de ingeniería (capa ②)

| Repo | Familia | Algoritmo nuclear | Stack |
|---|---|---|---|
| **Noel** | E1 | A\* (Manhattan) + replan | **Poetry**, flake8, mypy laxo, pdb, ANSI. **Sin tests, sin CI.** |
| **Jose** | E1+ | Dijkstra single-path + validador + fallback | **uv**, flake8, **mypy strict**, pytest, FastAPI/uvicorn/httpx, frontend HTML/JS, **CI (lint+lint-strict+test)**, hatchling |
| **Mario** | E2 | A\* exacto + 8 candidatos + estimador + deadlock detection | **uv**, flake8, **mypy strict**, pytest+**cov**, **FastAPI/pydantic v2**, frontend **JS+SVG**, **CI**, setuptools, Python 3.12 |
| **Ariel** | E4 | **WHCA\*** + reservas + holds | venv, flake8, mypy laxo, pytest, **pygame-ce**, **ABC/Protocol**, docs enormes. **Sin CI.** |

> **Corrección verificada:** Mario **no** usa React. El frontend es **JS vanilla + SVG**; FastAPI sí
> está implementado (`backend/src/flyin/adapters/api/`).

### 6.2 Granularidad real (historial `git` completo, no `--depth 1`)

| Repo | Commits | Período | Branches/PRs | Mensajes | Horizonte |
|---|---|---|---|---|---|
| **Noel** | **6** | 1 día (25-feb) | ✗ | Español informal | "raid" de un día |
| **Ariel** | **22** | 6 semanas (27-ago→09-oct) | ✗ | Informal ("semisólido", "últimos retoques") | iterativo |
| **Mario** | **135** | 5 semanas (11-jul→19-ago) | ✅ `agent/*` + PRs #76–81 | **Conventional Commits** (`feat:`/`fix:`/`chore:`/`perf:`) | altísimo |
| **Jose** | **177** | 5 semanas (17-jul→22-ago) | ✅ `chore/*`,`feat/*`,`docs/*` + PRs #91–97 | Imperativo + prefijos | altísimo |

**Lectura:** la **granularidad de commits** es una señal de mercado directa y acá separa aguas.
Mario y Jose trabajaron como equipo profesional (atómicos + PRs + CI); Ariel y Noel, en "modo
entrega". Fijate que **Ariel tiene el mejor algoritmo pero el git más flojo** de los cuatro.

### 6.3 Patrones, granularidad de módulos y "AI-workflow" (capa ③)

| Repo | Archivos src/test | Patrones observados | Workflow con IA |
|---|---|---|---|
| **Noel** | 15 / 0 | `@dataclass` + Factory | ✗ |
| **Jose** | 43 / 18 | `@dataclass` inmutables (domain) + Validator | ✅ `.claude/`, `CLAUDE.md` |
| **Mario** | 40 / 23 | `@dataclass` modelos inmutables + Estimator/Validator | ✅ `.agents/`, `AGENTS.md`, `hermes/` |
| **Ariel** | 30 / 12 | **ABC / abstractmethod** (observer) + `Protocol`/`Generic` | ✗ |

- **Dataclasses inmutables** (Jose, Mario) → reproducibilidad y modelos limpios. Muy valorado.
- **ABC/Protocol** (Ariel) → el OOP más "formal". Buena señal, pero más superficie.
- **AI-workflow** (Jose, Mario) → **habilidad de 2026**: instruir agentes (`CLAUDE.md`/`AGENTS.md`) y
  trabajar con branches `agent/*` + PRs. Esto es **literalmente tu día a día** como dev moderno.

---

## 7. Los algoritmos como activo (capa ① puesta en perspectiva)

| Algoritmo | Aparece en | Dónde se usa en la industria | ¿Pesa en entrevista? |
|---|---|---|---|
| **Dijkstra / A\*** | todos | Mapas, navegación, pathfinding de juegos, redes | **Sí, siempre** |
| **Node-disjoint paths** | E2 (Sabofxx/Mario) | Redes redundantes, telecom | Medio |
| **Scheduling con capacidades / makespan** | E2 | Job-shop, flotas, Kubernetes (bin-packing) | **Sí, en sistemas** |
| **MCMF / flujo** | E3 | Logística, matching, assignment | Medio (nicho) |
| **MAPF / WHCA\*** | E4 | **Robótica, almacenes (Amazon), juegos** | **Señal senior** |
| **Reservation tables** | E4 | Planificación multi-agente | Alto en robótica |

> **Conclusión:** E2 te da **Dijkstra + A\* (obligatorios) + scheduling (muy pedido)**. E4 suma
> **MAPF (diferenciador senior)**. E1 solo te da lo básico. E3 es un extra de nicho.

---

## 8. Escalabilidad: la letra chica (te la van a preguntar)

| Encuadre | Costo por turno | Costo de planificación | ¿Crece bien si N↑, V↑? |
|---|---|---|---|
| **E1** | `O(N·grado)` | `O((V+E) log V)` (+replan caro) | **Regular** (embudo + replan) |
| **E2** | `O(T·N·grado)` | `O(k·(V+E) log V)` + subconjuntos acotados | **Bien** (combinatoria controlada) |
| **E3** | `O(T·N·grado)` (tras flujo) | `O(N·E log V)` | **Bien** (pero caja negra) |
| **E4** | — | `O(N·Z·W·grado·log(Z·W))` por ronda | **La mejor** por agente |

> **Lo que tienen que decir en defensa:** "N es chico (≤44 en el challenger), así que la
> escalabilidad real **no** es el cuello; el cuello es la **calidad del schedule** (makespan) y el
> **control de la combinatoria** de caminos". Eso demuestra criterio de ingeniería.

---

## 9. Tecnologías y hábitos que te llevás (ranking para tu formación + mercado)

Ordenados por **(transferibilidad × valor de mercado) ÷ curva de aprendizaje**:

| # | Activo | Capa | Curva | ¿Por qué te lo llevás? |
|---|---|---|---|---|
| 1 | **`uv` + `pyproject.toml`** | ② | Baja | El estándar moderno de proyectos Python. Lo usás en todo. |
| 2 | **`pytest` (+ `pytest-cov`)** | ② | Baja | Testing es obligatorio para ser "serio". |
| 3 | **`mypy --strict`** | ② | Media | Pensar en tipos te cambia la cabeza; el subject ya lo pide. |
| 4 | **`git` profesional** (branches, PRs, conventional commits) | ③ | Media | Es tu carta de presentación en GitHub. |
| 5 | **CI con GitHub Actions** | ② | Media | Separar "estudiante" de "profesional". |
| 6 | **`flake8`** | ② | Baja | Estilo consistente; el subject lo pide. |
| 7 | **Trabajar con agentes de IA** (`CLAUDE.md`/`AGENTS.md`) | ③ | Baja-media | Habilidad central de 2026. |
| 8 | **`argparse`** | ② | Baja | CLI idiomática; lo pide el subject. |
| 9 | **`pydantic` v2** *(opcional)* | ② | Media | Validación de datos; puerta a FastAPI/IA. |
| 10 | **`pygame-ce`** *(opcional)* | ② | Baja | Demo visual linda; no suma al algoritmo. |
| 11 | **`FastAPI`** *(fuera de alcance)* | ② | Media-alta | Muy pedido, pero el subject pide **CLI**. Guardalo para otro proyecto. |

> Las **1–8 las podés tener en un proyecto E1/E2 simple**. No necesitás el algoritmo difícil para
> aprender lo rentable.

---

## 10. Mapeo: tus 3 propuestas vs encuadres vs repos

| Tu propuesta | Encuadre | Repo que la valida | Qué cambia |
|---|---|---|---|
| **Propuesta A** (reverse Dijkstra + k node-disjoint + greedy + sim reactiva) | **E2** | Mario, Sabofxx | Versión "de manual" de E2. |
| **Propuesta B** (MCMF + node-splitting) | **E3** | lem-in; ninguno de los 4 | Reemplaza la selección de caminos por flujo. |
| **Propuesta C** (Space-Time A\* + reservas) | **E4** | Ariel (WHCA\*), codebit-hub | Cambia el simulador reactivo por cooperación temporal. |

---

## 11. Matriz de decisión ponderada (6 lentes)

Pesos propuestos para tu perfil (rápido + simple + defendible, pero valorando mercado). **Ajustables.**

| Lente | Peso |
|---|---|
| L1 Velocidad | 0.20 |
| L2 Baja complejidad | 0.20 |
| L3 Defendibilidad | 0.15 |
| L4 Valor formativo | 0.15 |
| L5 Transferibilidad | 0.15 |
| L6 Valor de mercado | 0.15 |

| Encuadre | L1 | L2 | L3 | L4 | L5 | L6 | **Total** | Gate aprobación |
|---|---|---|---|---|---|---|---|---|
| **E1** | 5 | 5 | 5 | 2 | 3 | 2 | **3.80** | ⚠️ medio |
| **E2** ⭐ | 4 | 3.5 | 4 | 5 | 5 | 5 | **4.35** | ✅ bajo |
| **E4** | 2.5 | 2 | 3 | 5 | 4.5 | 5 | **3.53** | ✅ bajo |
| **E3** | 2 | 1.5 | 3 | 5 | 3.5 | 4.5 | **3.10** | ✅ bajo |

**Lectura con el nuevo peso de mercado:** ahora **E2 gana con claridad**. E1 cae porque, aunque
sea rapidísimo, **no deja señal de mercado** (L6=2) ni aprendizaje (L4=2). E4 es fuerte en mercado
pero caro en tiempo/riesgo. E3 no compite.

> Si subís **velocidad** a 0.35 y bajás **mercado** a 0.05, E1 se acerca a E2 otra vez — pero E1
> sigue con el **gate ⚠️** de aprobación. En casi cualquier perfil razonable, **E2 gana**.

---

## 12. Recomendación y orden de ataque

### Recomendación
> **E2 (Propuesta A) + ingeniería de nivel mercado.**
> - **Algoritmo (①):** Dijkstra/A\* exacto + k caminos + estimador de makespan + scheduler con reservas + **validador independiente**.
> - **Ingeniería (②):** `uv` + `pyproject` + `flake8` + `mypy --strict` + `pytest` + CI + `argparse`.
> - **Cultura (③):** `git` con branches/PRs/**conventional commits**; trabajar con agente de IA (`CLAUDE.md`/`AGENTS.md`).
> - **NO:** FastAPI, frontend, MCMF, WHCA\* (salvo bonus).

**Por qué:** es el único que **pasa todo (43) + te enseña de verdad + deja señal de mercado fuerte**,
sin el dolor de cabeza del flujo ni del espacio-tiempo. El **validador independiente** es tu mejor
arma de defensa: *"un componente que re-deriva las reglas y verifica cada turno; si algo no cumple,
el programa lo grita"*.

**Por qué NO E3/E4 como camino principal:** E3 = dominio nuevo + bugs silenciosos (ningún repo de
los 4 lo necesitó). E4 = bonus **post-E2** si sobra tiempo (ahí sí justificás el récord de 43).

### Orden de ataque (8 pasos, ~7–8 días de foco)
1. **Parser + validación** del formato — _0.5 d_
2. **Modelo de grafo** (zonas, conexiones, capacidades, costos, tipos) — _0.5 d_
3. **PathFinder** (Dijkstra/A\*) detrás de una **interfaz** (ABC/Protocol) — _1 d_
4. **Simulador** (fases decidir/aplicar/verificar) con **FSM por drone** — _1–1.5 d_
5. **Formateador de salida** (turnos; restricted `D<id>-<origen>-<destino>`) — _0.5 d_
6. **Tooling + cultura**: Makefile (`install run debug clean lint lint-strict`) + `uv` + `pytest` + `mypy` + `flake8` + **CI** + conventional commits — _1 d_
7. **Salto a E2**: k caminos + allocator + estimador + **validador** — _2–3 d_
8. **(Opcional) E4**: WHCA\* si sobra tiempo — _4–6 d_

---

## 13. Dolores de cabeza a evitar (antipatrones)

| Antipatrón | Por qué duele | Cómo evitarlo |
|---|---|---|
| **Hexagonal + DDD + API + frontend** para un CLI | Superficie de defensa enorme; tiempo fuera de alcance | Módulos claros **sin** API ni frontend |
| **MCMF / teoría de flujo** | Dominio nuevo + bugs silenciosos | Mencionalo en la defensa; no lo codees |
| **WHCA\* sin límite de seguridad** | Cuelgues o choques "imposibles" | Límite `drones×zonas×4` + hold provisional |
| **React / frontend web** | El subject pide **CLI** | ANSI colors + (opcional) `--visual` con pygame |
| **Replan (Dijkstra) cada turno** | `O(turnos × Dijkstra)` | Replan solo al bloquearse → o pasá a reservas (E2) |
| **Estado global mutable en el simulador** | Bugs irreproducibles | **FSM explícita por drone** + fases |
| **`git` en 2 commits gigantes** | No muestra trabajo ni permite revisión | **Commits atómicos** + PRs (**mirá a Mario/Jose**) |
| **Tests al final** | Nunca se escriben | Escribí el **validador** y usalo como test |

---

## 14. Resumen (7 líneas)

1. **Algoritmo por riesgo de aprobación → E2. Ingeniería y cultura por aprendizaje+mercado.**
2. E2 pasa todo (43), es el que **más enseña** y el que **mejor señal de mercado** deja.
3. **Validador independiente** = tu mejor defensa.
4. **Granularidad** (commits/módulos/tests) y **`git` profesional** son señal de mercado directa.
5. **Escalabilidad**: N es chico; el cuello real es la **calidad del schedule**, no el tamaño.
6. **E3 no compite**; **E4 es bonus** post-E2 (y ahí justificás el récord).
7. Evitá API/frontend/hexagonal que el subject no pide.

---

## 15. Cierre — qué mirar de cada repo

| Querés aprender… | Mirá en… |
|---|---|
| Estructura mínima que aprueba (sin sobre-ingeniería) | **Noel** (`domain/` + `infrastructure/`) |
| Validador independiente + fallback + **CI de 3 jobs** | **Jose** (`schedule_validator.py`, `.github/workflows/ci.yml`) |
| Estimador de makespan + elegir caminos + **dataclasses inmutables** | **Mario** (`scheduling/metrics.py`, `allocator.py`) |
| **ABC/Protocol** + cooperación espacio-temporal (bonus) | **Ariel** (`pathfinding/whca.py`, `reservation_table.py`) |
| **`git` profesional + workflow con agentes** | **Mario/Jose** (PRs, conventional commits, `AGENTS.md`/`CLAUDE.md`) |

> Clones (historial completo) en `/tmp/opencode/repos/{noel,mario,ariel,jose}` para relectura.

---

## 16. Conclusión — qué cambió de perspectiva y qué falta preparar

> Esta sección cruza **(a)** lo que hacen los 4 programadores, **(b)** lo que propuse en
> `propuestas_resolucion.md` (Propuestas **A/B/C**) y **(c)** el encuadre **E2** de este documento.
> El objetivo es dejar registrado **cómo cambió la prioridad de la estructura** y **qué planes de
> diseño quedan pendientes de preparar**.

### 16.1 Qué confirman los 4 repos sobre MIS propuestas A/B/C

| Mi propuesta | Qué dice la evidencia | Veredicto |
|---|---|---|
| **A — Simulación reactiva** (k=min(4,N) caminos + asignación greedy + sim por turnos) | Es **exactamente la base** que ejecutan Noel y Jose, y que funciona. Confirma que arrancar por acá es correcto. | ✅ **Instinto correcto**: es la base. Pero **A "pelada"** deja makespan en la mesa (no reparte bien el tráfico). |
| **B — MCMF (flujo)** | **Ninguno** de los 4 la necesitó para aprobar. | ⚠️ **Elegante pero no requerida**: queda como argumento de defensa, no como código. |
| **C — Space-Time A\*** | **Ariel** demuestra que es la vía al **récord (43)**. | 🏆 **Válida, pero cara**: solo como bonus post-E2. |

**El hallazgo central:** **E2 = A + 3 refinamientos** que saco de los repos. No es "otro plan":
es **mi Propuesta A, endurecida** con piezas ya probadas:

1. **Estimador de makespan** para elegir *cuántos* caminos usar → de **Mario**.
2. **Scheduler con reservas de capacidad + detección de deadlock** → de **Mario**.
3. **Validador independiente** (un juez que re-deriva las reglas) → de **Jose/Mario**.

> Traducción simple: **B y C eran "cambiar el motor"; E2 es "afinar el motor que ya tenías".**
> Mario es, literalmente, mi Propuesta A + esos 3 refinamientos.

### 16.2 El cambio de perspectiva (se movió el eje)

**Antes** (mis propuestas): el eje era **"¿qué algoritmo?"** → una escalera **A → B → C** ordenada
por *techo de calidad* (hasta dónde llega el makespan).

**Ahora** (con la evidencia de los 4 repos): el eje es **"¿qué estructura + qué ingeniería?"**.
La prioridad quedó así, de mayor a menor:

| Prioridad | Qué es | Por qué subió/bajó |
|---|---|---|
| **1. Correctitud + estructura simple** | Factibilidad primero; capas por responsabilidad (parser/dominio/pathfinding/simulación/render) | **No negociable.** Los 4 repos la respetan; es la base que aprueba. |
| **2. Ingeniería y cultura** | tests, `mypy --strict`, CI, `git` granular (PRs + conventional commits), trabajar con agentes de IA | **Subió fuerte.** Es barato de agregar y es lo que más te forma y más te vende. |
| **3. Refinamiento MEDIDO del algoritmo** | E2: estimador + scheduler con reservas + validador | **Es donde está la nota**: se gana calidad sin teoría nueva. |
| **4. Algoritmo "estrella"** | E4 (WHCA\*), E3 (MCMF) | **Bajó a bonus.** Ningún repo lo necesitó para aprobar. |

**La prueba del cambio:** Mario y Jose (algoritmo **E1/E2**, más simple) **superan** a Ariel
(algoritmo **E4**, el mejor) en señales de mercado: **135/177 commits** con PRs y CI vs **22 commits
informales sin CI**. *El conjunto pesa más que el truco algorítmico.* El algoritmo estrella gana el
récord; **no te salva si el `git` y los tests están flojos.**

**Y la prioridad cambió la ESTRUCTURA elegida:** ya no alcanza con "una capa por responsabilidad".
La estructura de E2 agrega **dos componentes que son jueces**:

- **Estimador** → *decide* qué caminos convienen (antes de simular).
- **Validador** → *audita* cada turno contra las reglas (después de simular).

> El **validador deja de ser un extra y pasa a ser pieza de primera clase**. Es, a la vez, tu
> mejor defensa y tu mejor suite de tests. Eso **no** estaba en mi Propuesta A original.

### 16.3 Los planes de diseño que faltan preparar

> **⚠️ ESTADO ACTUALIZADO (posterior a la redacción de este documento).** Esta tabla se escribió el
> **10-oct 19:36**; entre **19:45 y 20:07** del mismo día se crearon los documentos que resuelven
> los ítems **1 a 4**. Solo el **ítem 5 (esqueleto de repo)** sigue pendiente. La fila tachada de
> abajo queda como registro histórico de lo que estaba abierto al momento de la comparativa.

| # | Plan | Contenido | Documento (evidencia) | Estado REAL |
|---|---|---|---|---|
| 1 | **Cerrar decisiones abiertas** | token de conexión;¿`cap(e)` en tránsito?; ¿mapas `.txt`?; prioridad mandatory vs challenger | `plan_implementacion_E2.md` §6 (D1–D5) | ✅ **CERRADO** (D1–D5; solo **D2b** con default + flag) → ya **no bloquea** al design |
| 2 | **Spec (SDD)** | Requisitos + escenarios: transit, swap, capacidades, formato exacto de salida | `spec_E2.md` (v0.1, 553 líneas) | ✅ **HECHO** |
| 3 | **Design doc** | Arquitectura E2: capas, interfaces, invariantes, contrato de salida | `plan_estructuracion_E2.md` (329 líneas) | ✅ **HECHO** |
| 4 | **Task breakdown** | Orden de ataque (§12) → tareas atómicas por fase | `plan_implementacion_E2.md` (F0–F9) + `cronograma_E2.md` | ✅ **HECHO** |
| 5 | **Esqueleto de repo** | Layout de carpetas + `pyproject` + `uv` + Makefile + `mypy`/`flake8` + CI + `git` granular | — | 🔲 **PENDIENTE** (único ítem vivo; no hay `pyproject.toml`, `src/`, `Makefile`, `.github/` ni `.git`) |

> **Nota:** a partir de acá la **fuente de verdad** son `spec_E2.md` (QUÉ), `plan_estructuracion_E2.md`
> (CÓMO) y `plan_implementacion_E2.md` (orden). Esta comparativa queda como **registro de la decisión**
> (por qué E2), no como plan operativo.

### 16.4 Cierre en una frase

> **Un algoritmo correcto pero a medias (A) aprueba. Un algoritmo correcto + estructura simple +
> buena ingeniería (E2) aprueba, te enseña y te vende. Un algoritmo estrella (C/E4) gana el récord,
> pero no te salva si el `git` y los tests están flojos.**

**Lo que tenemos que preparar, en orden (actualizado):** ✅ decisiones cerradas → ✅ **spec → design →
tasks** hechos → 🔲 **esqueleto de repo** (F0 de `plan_implementacion_E2.md`) → implementar **F1–F8**
(E2) → bonus **E4** (F9) si sobra tiempo.
