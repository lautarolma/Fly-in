# Fly-in — Plan de estructuración E2 (teórico / didáctico)

> **Documento VIVO.** Se revisa y reestructura durante la implementación, a medida que aparecen
> planteos nuevos. Versión inicial: `v0.1`.
>
> **Rol de este documento:** explicar **QUÉ estructura vamos a construir y POR QUÉ**, con la
> fundamentación teórica y didáctica. No es el "cómo paso a paso" (eso es
> `plan_implementacion_E2.md`) ni el calendario (eso es `cronograma_E2.md`).
>
> **Encuadre:** E2 — *K-caminos + asignación + scheduler validado*, según
> `comparativa_propuestas.md`.
>
> **Filo conductor:** *correctitud primero, ingeniería siempre, optimización medida después.*

---

## 0. Cómo usar este documento

- Leelo **antes** de codear cada componente: te da el "para qué" y el "por qué" de cada decisión.
- Cuando choques con un problema que cambie la estructura, **actualizá acá** (§ correspondiente) y
  recién después tocá el código.
- Cada sección de arquitectura termina con un bloque **"Para la defensa"**: la frase corta que
  explica esa decisión en la oral.

---

## 1. El modelo mental (qué estamos resolviendo)

Antes de cualquier clase, entendamos el problema. Si esto no está claro, el código no se defiende.

- **Es un grafo** `G = (V, E)`: nodos = **zonas**, aristas = **conexiones**.
- **El tiempo es discreto:** avanza en **turnos** `t = 0, 1, 2, …`. No hay reloj continuo.
- **Entrar a una zona cuesta según el DESTINO**, no la arista:
  - `normal` = 1 turno, `priority` = 1 turno (desempate), `restricted` = 2 turnos, `blocked` = ∞.
- **`restricted` es el caso especial:** el drone ocupa la **conexión** un turno entero (estado
  "en tránsito") y **está obligado** a entrar al destino al turno siguiente. *No puede quedarse en
  la conexión.*
- **Capacidades:** cada zona tiene `cap(v)` (default 1; `start`/`end` = ∞) y cada conexión `cap(e)`
  (default 1). En cada turno no puede haber más drones que la capacidad.
- **La semántica que lo cambia todo (swap):** *quien sale libera su capacidad ESE MISMO turno*.
  Entonces dos drones pueden **intercambiarse** zonas en el mismo turno. Si validás la capacidad
  **antes** de liberar las salidas, perdés turnos.
- **Objetivo:** minimizar el **makespan** = turnos hasta que llega el **último** drone.

**¿Qué problema es, en teoría?**
Es un **MAPF con capacidades** (Multi-Agent Path Finding) con **tránsitos multi-turno**. Más
formalmente, un **flujo sobre el tiempo** (*flow over time*) buscando el **quickest flow**.
Ambos son **NP-hard**: **no** buscamos el óptimo global, buscamos una **heurística correcta y buena**.

> **Regla de oro:** *factibilidad primero, makespan óptimo después.* Un simulador 100% correcto que
> respeta todas las capacidades **ya aprueba**. La optimización es incremental.

**Para la defensa:** *"Modelé el problema como MAPF con capacidades sobre tiempo discreto; como es
NP-hard, garanticé factibilidad con un simulador y optimicé el makespan con heurísticas."*

---

## 2. Los 3 pilares (orden de prioridad)

Este orden **no se negocia**. Es el aprendizaje central de la comparativa.

| Pilar | Qué es | Si falta… |
|---|---|---|
| **1. Factibilidad / estructura simple** | El programa corre, respeta reglas y capacidades, no cuelga | No aprobás. Nada más importa. |
| **2. Ingeniería** | Separación en capas, tests, `mypy --strict`, CI, `git` granular | Aprobás, pero no aprendés ni "vendés". |
| **3. Refinamiento medido** | k-caminos + estimador + scheduler + validador → mejor makespan | Aprobás, pero no llegás al challenger. |

> **Lo que NO es un pilar:** la elegancia teórica (flujo, MAPF óptimo). Es un **bonus**, nunca la base.

**Para la defensa:** *"Priorizé factibilidad, después ingeniería, y por último optimización: un
sistema correcto y mantenible vale más que uno óptimo y frágil."*

---

## 3. La arquitectura por capas

**Pipeline unidireccional** (los datos fluyen en una sola dirección, sin ciclos):

```
 [input.txt]
     │
     ▼
 ┌─────────┐
 │ Parser  │  texto → objetos de dominio (o error con línea + causa)
 └────┬────┘
      ▼
 ┌──────────────┐
 │ Domain/Graph │  zonas, conexiones, capacidades, vecinos
 └──────┬───────┘
        ▼
 ┌────────────┐
 │ PathFinder │  → k caminos candidatos (con costos)
 └─────┬──────┘
       ▼
 ┌──────────────┐
 │ RouteBuilder │  construye/selecciona el set de rutas posibles
 └──────┬───────┘
        ▼
 ┌────────────┐
 │ Estimator  │  ★ JUEZ 1 → estima el makespan de cada reparto posible
 └─────┬──────┘
       ▼
 ┌────────────┐
 │ Scheduler  │  asigna drones a rutas (política)
 └─────┬──────┘
       ▼
 ┌────────────┐
 │ Simulation │  avanza turnos: decidir → aplicar → (verificar)
 └─────┬──────┘
       ▼
 ┌────────────┐
 │ Validator  │  ★ JUEZ 2 → re-deriva las reglas y audita cada turno
 └─────┬──────┘
       ▼
 ┌────────────┐
 │  Renderer  │  salida coloreada por terminal + líneas oficiales
 └────────────┘
```

### 3.1 Responsabilidades (SRP: una razón para cambiar cada una)

| Componente | Responsabilidad única | Qué **NO** hace |
|---|---|---|
| `Parser` | texto → dominio; errores con línea y causa | pathfinding, decidir |
| `Domain` (`Graph`, `Zone`, `Connection`) | topología y capacidades; consultas de vecinos | simular |
| `PathFinder` | distancias y caminos (Dijkstra / A\*) | conocer drones ni turnos |
| `RouteBuilder` | armar el conjunto de k rutas candidatas | asignar a drones |
| `Estimator` | estimar el makespan de un reparto | simular de verdad |
| `Scheduler` | asignar drones a rutas | avanzar el reloj |
| `Simulation` | avanzar el turno, validar ocupación, emitir movimientos | parsear / decorar |
| `Validator` | auditar un schedule contra las reglas | decidir / optimizar |
| `Renderer` | mostrar estado (colores) | tomar decisiones |

### 3.2 Por qué esta separación (didáctico)

- **Testeabilidad:** cada caja se testea sola. El `Parser` con strings, el `PathFinder` con grafos
  armados a mano, el `Simulation` con mapas chicos. **Sin capas, todo se testea junto y no sabés
  dónde falló.**
- **Extensibilidad:** el `PathFinder` está detrás de una **interfaz** → podés enchufar MCMF (E3) o
  Space-Time A\* (E4) **sin tocar** el simulador. (Principio Abierto/Cerrado.)
- **Defensa:** cada capa es un "tema" que podés explicar en 30 segundos.

**Para la defensa:** *"Es un pipeline unidireccional donde cada etapa tiene una única
responsabilidad; eso me permite testear y explicar cada parte por separado, y reemplazar el
algoritmo de búsqueda sin tocar la simulación."*

---

## 4. El modelo de datos

**Decisión:** usar `@dataclass(slots=True, frozen=True)` para las entidades del dominio.

```python
class ZoneType(Enum):
    NORMAL = "normal"; PRIORITY = "priority"
    RESTRICTED = "restricted"; BLOCKED = "blocked"

@dataclass(slots=True, frozen=True)
class Zone:
    name: str
    x: int; y: int
    type: ZoneType
    cap: int | None          # None = ∞ (start/end)
    color: str | None

@dataclass(slots=True, frozen=True)
class Connection:
    a: str; b: str           # clave canónica: tuple(sorted((a, b)))
    cap: int

Grafo: zones: dict[str, Zone]; adj: dict[str, dict[str, Connection]]
Drone: id | path: list[str] | index | state: DroneState (WAITING/IN_TRANSIT/DELIVERED)
```

### 4.1 ¿Por qué `frozen=True`? (didáctico)

- **Inmutables ⇒ seguras:** nadie te cambia una `Zone` por accidente a mitad de la simulación.
- **Hashables:** podés usarlas como clave (ej.: reservas `(zona, turno)`).
- **Reproducibilidad:** el mismo input da el mismo output, siempre (clave para debuggear y defender).
- **Señal de calidad:** es lo que hacen Mario y Jose; el evaluador lo reconoce.

**El estado del drone es una FSM** (máquina de estados): `WAITING → IN_TRANSIT → DELIVERED`.
Ya la usás en call_me_maybe; acá el drone es el autómata.

**Para la defensa:** *"Mis entidades son inmutables y el drone es una máquina de estados de tres
fases; eso elimina clases enteras de bugs y hace la simulación reproducible."*

---

## 5. Las dos piezas-juez (lo que E2 agrega a la Propuesta A)

Esta es la diferencia entre "un simulador que anda" y E2.

### 5.1 Estimador (JUEZ 1) — decide ANTES de simular

- **Qué hace:** dada una posible selección de rutas, **estima** cuántos turnos va a tardar el
  conjunto, **sin simular**. Cota estilo lem-in:
  - por ruta: `costo_i + carga_i − 1`
  - por recurso: `⌈carga / capacidad⌉ − 1 + costo`
  - el makespan estimado = **máximo** de esas cotas.
- **Por qué sirve:** te da un **criterio para elegir cuántas rutas usar** en vez de adivinar. Si
  tener 4 rutas no baja la cota, no las generes.
- **Dónde lo robamos:** `FleetMakespanEstimator` de **Mario**.

### 5.2 Validador (JUEZ 2) — audita DESPUÉS de simular

- **Qué hace:** toma el schedule producido y **re-deriva todas las reglas** (capacidades, transit,
  swap, coherencia del output). Si algo no cumple → lo grita.
- **Por qué es pieza de primera clase:**
  1. **Es tu mejor defensa:** *"tengo un juez independiente que verifica cada turno"*.
  2. **Es tu mejor suite de tests:** corrés el validador sobre todos los mapas.
  3. **Rompe el acoplamiento:** el simulador optimiza; el validador juzga. Un validador
     **independiente** no puede "hacer trampa" compartiendo código con el simulador.
- **Dónde lo robamos:** `ScheduleValidator` de **Jose/Mario**.

> **Idea de diseño:** *separá al que decide del que juzga.* Es el mismo principio que en testing:
> el test no comparte lógica con el código que testea.

**Para la defensa:** *"Tengo dos componentes-juez: el estimador decide la mejor estrategia antes de
simular, y el validador audita cada turno después, de forma independiente."*

---

## 6. Interfaces y extensibilidad (el Strategy)

- `PathFinder` es una **interfaz** (`ABC` o `Protocol`): un método `find(gas)` que devuelve caminos.
- Implementaciones: `DijkstraPathFinder` (base), y **enchufables** sin tocar nada más:
  `AStarPathFinder`, `MCMFPathFinder` (E3), `SpaceTimePathFinder` (E4).
- **Regla anti-sobre-ingeniería:** usar `ABC`/`Protocol` **solo donde hay >1 implementación real o
  prevista**. No abstraigas todo "por las dudas".

**Para la defensa:** *"El buscador de caminos está detrás de una interfaz; puedo cambiar el
algoritmo sin tocar la simulación — eso es el principio Abierto/Cerrado aplicado."*

---

## 7. Principios de diseño (mapa para la defensa)

- **SRP:** cada componente de §3.1 tiene una única responsabilidad.
- **Open/Closed:** agregar un `PathFinder` alternativo no toca al `Simulation`.
- **Interface Segregation:** interfaces chicas (`Renderer.render(...)`), no "diosas".
- **Dependency Inversion:** `Simulation` depende de abstracciones (`Graph`, `Path`, `Drone`), no
  del `Parser`.
- **SoC (separación de incumbencias):** parseo ≠ dominio ≠ búsqueda ≠ simulación ≠ presentación.

---

## 8. Anti-sobre-ingeniería (lo que NO vamos a construir)

Aprendido de la comparativa (Mario tiene ~7k LOC: el doble de lo necesario para aprobar).

| Tentación | Por qué la evitamos |
|---|---|
| Hexagonal + DDD + casos de uso | Superficie de defensa enorme; no suma nota |
| API (FastAPI) + frontend | El subject pide **CLI**; es un sumidero de tiempo |
| Sistema de plugins / factory de algoritmos | Una función + una interfaz alcanza |
| Motor genérico de eventos / observers | El loop de turnos es secuencial y simple |
| GUI compleja (pygame/matplotlib) | El render por terminal **cumple el requisito literal** |
| DI container | Pasar dependencias por constructor es suficiente |
| Recalcular caminos por turno "por si acaso" | **Causa #1 de timeouts**; cachear 1 vez |

> **Principio rector:** el subject premia **correctitud + explicabilidad + un algoritmo eficiente**,
> no un framework. Menos abstracción = menos bugs y menos superficie para defender.

---

## 9. Los invariantes duros (qué hay que testear sí o sí)

1. **`restricted` transit:** ocupar la conexión 1 turno + llegada obligada al siguiente.
2. **Swap:** validar capacidad **después** de liberar salidas.
3. **Capacidades** de zona y conexión nunca excedidas en un turno.
4. **`start`/`end` sin límite** de capacidad.
5. **Alcanzabilidad:** si `end` queda aislada por `blocked` → error claro, no loop infinito.
6. **Formato de salida:** separadores, orden y el token de conexión exacto.

Estos 6 son los que **más review-te van a hacer** y los que **más bugs** generan. El `Validator`
(§5.2) existe para cubrirlos.

---

## 10. Conceptos a estudiar (didáctico)

| Concepto | Por qué | Dónde aparece |
|---|---|---|
| **Dijkstra / cola de prioridad** | Camino más corto con pesos | `PathFinder` |
| **Heurística admisible + A\*** | Búsqueda dirigida a la meta | `PathFinder` (bonus) |
| **Máquina de estados (FSM)** | Estado del drone | `Simulation` |
| **`@dataclass(frozen=True)`** | Inmutabilidad y reproducibilidad | `Domain` |
| **Cota de makespan (lem-in)** | Elegir rutas sin simular | `Estimator` |
| **Caminos node-disjoint / penalización** | Repartir tráfico | `RouteBuilder` |
| **Scheduling con recursos** | Asignar y reservar capacidades | `Scheduler` |
| **Testing de invariantes** | Garantizar las reglas duras | `Validator` + tests |
| **Tipado estático (`mypy`)** | Detectar bugs antes de correr | Todo el repo |

---

## 11. Errores comunes (pitfalls)

- **Validar capacidad antes de liberar salidas** → perdés el swap y sumás turnos.
- **Confundir `priority` con peso 0** → sigue costando 1 turno; es solo desempate.
- **Recalcular Dijkstra cada turno** → lento; cachear o usar reservas.
- **Estado global mutable en el simulador** → bugs irreproducibles; usá FSM explícita.
- **Dejar el formato de salida para el final** → la evaluación lo parsea; fijalo temprano.
- **Testear al final** → nunca pasa; usá el `Validator` como test.

---

## 12. Preguntas que condicionaron la estructura (✅ TODAS CERRADAS)

Estas **bloquearon** decisiones de diseño y ya están resueltas (ver `propuestas_resolucion.md` §8–9 y
el registro de decisiones en `plan_implementacion_E2.md` §6):

1. **Token de conexión en tránsito** — ✅ **cerrada (D1):** `D<id>-<origen>-<destino>` (dirección de
   viaje, strings del input).
2. **`cap(e)` durante el tránsito** — ✅ **cerrada (D2/D2b):** sí consume capacidad; por defecto la
   ocupación dura **todo el tránsito** (2 turnos), aislada tras un flag.
3. **Mapas `.txt`** — ✅ **cerrada (D3):** los **provee el usuario** (no se reconstruyen).
4. **Prioridad** — ✅ **cerrada (D4):** **mandatory primero**; challenger solo tras el Hito M3.
5. **Prefijo de turno en la salida** — ✅ **cerrada (D5):** sin prefijo (subject §VII.5).

> Con **todas** las decisiones cerradas (D1, D2/D2b, D3, D4, D5), el `Renderer` y el `Scheduler`
> **se congelan**. La única observación viva es la **duración exacta** de la ocupación de la conexión
> (D2b), con default seguro (todo el tránsito) y flag para medir.

---

## 13. Glosario

Ver `comparativa_propuestas.md` §0 (glosario completo de algoritmos, ingeniería y stack).
