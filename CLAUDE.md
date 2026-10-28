# CLAUDE.md

See **[AGENTS.md](./AGENTS.md)** for the full working agreements and domain contract.

Quick reference for this project (Fly-in, 42, strategy E2):

- Layout: `src/flyin` (src layout), tests in `tests/`.
- Zero runtime dependencies; stdlib only; `networkx`/`graphlib` forbidden.
- Tooling: `uv` + `flake8` + `mypy --strict` + `pytest`. Run `make lint` / `make test`.
- Plans & specs live in `docs/` — the subject (`~/Python/Subjects/Fly-in/`) always wins.
- Conventional Commits, atomic; no AI attribution.
