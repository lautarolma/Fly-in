# Fly-in — Makefile (targets mandated by the subject, Chapter III.2)
# install · run · debug · clean · lint · lint-strict   (+ test)

PY    ?= python3
MAP   ?= maps/easy/01_linear_path.txt
PKG   := src/flyin
MYPY_FLAGS := --warn-return-any --warn-unused-ignores --ignore-missing-imports \
	--disallow-untyped-defs --check-untyped-defs

.PHONY: install run debug clean lint lint-strict test

install:
	uv sync

run:
	uv run fly-in $(MAP)

debug:
	uv run python -m pdb -m flyin $(MAP)

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .coverage htmlcov build dist *.egg-info

lint:
	uv run flake8 .
	uv run mypy . $(MYPY_FLAGS)

lint-strict:
	uv run flake8 .
	uv run mypy . --strict

test:
	uv run pytest
