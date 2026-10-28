# AGENTS.md — working agreements for AI agents (Fly-in)

## Source of truth (read before acting)
1. `~/Python/Subjects/Fly-in/Fly-in Subjct.md` — the subject. **It always wins.**
2. `docs/spec_E2.md` — WHAT (requirements + scenarios).
3. `docs/plan_estructuracion_E2.md` — HOW (architecture, rationale).
4. `docs/plan_implementacion_E2.md` — order (F0–F9) + decisions D1–D5.
5. `docs/cronograma_E2.md` — schedule and milestones.

## Hard rules
- Package layout: `src/flyin` (src layout). Import as `flyin.*`.
- Runtime deps = **zero**. stdlib only. Graph libraries (`networkx`, `graphlib`) are **forbidden**.
- Every function typed. `make lint-strict` (flake8 + `mypy --strict`) must stay green.
- Commits: Conventional Commits, atomic. Never add AI attribution/Co-Authored-By.
- Never let `main` be broken: work on branches, keep tests + lint green per commit.

## Domain contract (do not drift)
- Entering a zone costs by the **destination** type: `normal`=1, `priority`=1 (tie-break only),
  `restricted`=2, `blocked`=impassable.
- Capacity is evaluated **after** leavers free their slots (enables swaps, same turn).
- `restricted` transit occupies the connection and **must** arrive next turn (no waiting).
- Output: one line per turn, **no turn prefix**, waiting drones omitted, delivered drones never
  re-emitted. Transit token: `D<id>-<origin>-<destination>` (travel direction).
- The schedule `Validator` is an **independent** judge: it re-derives rules and shares **no logic**
  with the simulator. Input validation lives in `parsing`, not in the validator.

## Workflow per task
Context (files/layers) + contract (signature/in/out) + **tests it must satisfy** + explain
trade-offs. Review before committing.
