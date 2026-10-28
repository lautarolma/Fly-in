*This project has been created as part of the 42 curriculum by laviles.*

# Fly-in

## Description

Fly-in routes a set of drones from a unique `start_hub` to a unique `end_hub` over a weighted,
capacitated graph, in the fewest possible simulation turns (makespan). Movement is discrete and
simultaneous; zones and connections have capacities; `restricted` zones cost two turns to enter.

The engine follows strategy **E2**: exact shortest paths (Dijkstra/A\*) → k candidate routes →
makespan estimator → capacity-reserving scheduler → independent schedule validator.

Complexity and design notes live in `docs/`.

## Instructions

```bash
make install              # uv sync — install dependencies into .venv
make run MAP=maps/easy/01_linear_path.txt
make debug                # run under pdb
make lint                 # flake8 + mypy (subject flags)
make lint-strict          # flake8 + mypy --strict
make test                 # pytest
```

Direct usage:

```bash
uv run fly-in maps/easy/01_linear_path.txt
python -m flyin maps/easy/01_linear_path.txt
```

The program prints one line per simulation turn (space-separated drone movements) and exits with
code `0` on success, non-zero on any input error.

### Example

Input (`maps/easy/01_linear_path.txt`):

```
nb_drones: 2
start_hub: start 0 0 [color=green]
end_hub: goal 5 0 [color=yellow]
hub: mid 2 0 [zone=normal color=blue]
connection: start-mid
connection: mid-goal
```

Output:

```
D1-mid D2-mid
D1-goal D2-mid
D2-goal
```

## Resources

- 42 *Fly-in* subject (v1.6) — maps, capacity rules and output format.
- Graph algorithms: Dijkstra, A\*, node-disjoint paths.
- Scheduling: makespan bounds (lem-in style) and capacity reservations.
- **AI usage:** AI agents (opencode + SDD) were used for scaffolding, tests and docs; all algorithm
  design, invariants and defense decisions were made and reviewed by the author.

## Structure

```
src/flyin/   domain · parsing · pathfinding · routing · simulation · validation · rendering
tests/       unit · integration · fixtures
docs/        comparativa, spec SDD, plan de estructuración, plan de implementación, cronograma
maps/        easy · medium · hard · challenger
```
