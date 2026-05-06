# Work Journal

## Goal

Capture the reasoning, planning boundaries, and implementation decisions for the Liine take-home so the repo shows both the code and the workflow used to produce it.

## Assignment Framing

- Source of truth for requirements: `assignment.md`
- Source of truth for sample data: `restaurants.csv`
- Working prompt for staged execution: `prompt.md`
- We are intentionally not one-shotting the assignment. The work is broken into explicit planning and implementation stages.

## Shared Decisions

- Use Python for the implementation.
- Keep all tooling inside Docker.
- Expose the API outside the container.
- Use sqlite, FastAPI, SQLAlchemy, Pydantic, pytest, and uv.
- Use local wall-clock time for restaurant hours.
- Do not convert recurring business hours to UTC.
- Use separate sqlite databases for runtime and tests.
- Avoid database triggers for business-rule enforcement.
- Prefer simple, explicit architecture over clever abstractions.

## Prompt 1: Architecture And Repo Shape

### Planning Outcome

- Build a container-first scaffold before implementing domain logic.
- Keep the project structure small and conventional:
  - `app/api`
  - `app/core`
  - `app/db`
  - `app/etl`
  - `app/services`
  - `app/schemas`
  - `tests/unit`
  - `tests/integration`
- Expose container subcommands through one CLI entrypoint:
  - `serve`
  - `etl`
  - `test`
  - `fmt`
  - `lint`
- Add `README.md` and `AGENTS.md` early so the reviewer workflow is explicit from the start.

### Implementation Outcome

- Added the initial FastAPI scaffold with a `/health` endpoint.
- Added config and DB session wiring.
- Added Dockerfile, Makefile, and `pyproject.toml`.
- Added a smoke test.
- Left ETL and availability logic as explicit stubs to avoid bleeding into later prompts.

### Reviewer-Driven Fixes

- Updated `fmt` to run both `isort` and `black`.
- Changed `fmt` and `lint` to operate on the mounted working tree so formatting changes persist locally.
- Preserved host UID/GID for mounted `fmt` and `lint` runs to avoid root-owned files on Linux.
- Redirected tool caches to `/tmp` inside the container for mounted workflows.
- Added `.docker-data/` to `.gitignore`.

### Verification

- `make test` passes in Docker.
- `make lint` passes in Docker.

## Prompt 2: Data Model And Schedule Semantics

### Planning Outcome

We narrowed Prompt 2 after noticing it was starting to bleed into ETL design.

The agreed Prompt 2 implementation scope is:

- Add SQLAlchemy models for:
  - `restaurants`
  - `opening_intervals`
- Use `opening_intervals` as the table name instead of `open_blocks`.
- Store opening hours as minute-of-week intervals.
- Use half-open interval semantics: `[start, end)`.
- Enforce only simple structural constraints in the DB:
  - bounds
  - `start < end`
- Keep non-overlap enforcement in application code, not the database.
- Add pure domain helpers for stored-interval rules only:
  - minute-of-week representation
  - interval overlap checks
  - adjacency behavior
- Add unit tests for those stored-interval invariants.

### Explicit Non-Goals For Prompt 2

- No CSV parsing yet.
- No human-readable schedule parsing yet.
- No row-level ETL orchestration yet.
- No interval normalization from raw text yet.
- No week-wrap splitting implementation yet.
- No API query implementation yet.

### Notes

- Week wrap still matters as a future invariant because stored intervals should be non-wrapping.
- The actual split logic belongs to Prompt 3, when raw schedule strings are transformed into stored intervals.

### Implementation Outcome

- Added SQLAlchemy models for `restaurants` and `opening_intervals`.
- Chose minute-of-week as the stored representation for opening hours.
- Added DB-level structural constraints for interval bounds and `start < end`.
- Added pure domain helpers for minute-of-week conversion and overlap/adjacency checks.
- Added unit tests for stored-interval invariants and schema creation.

### Explicitly Deferred

- Parsing human-readable hours from `restaurants.csv`
- Row-level ETL validation and logging
- Interval normalization from raw text
- Any API query behavior beyond the existing healthcheck

## Why This Journal Exists

- The code alone does not show how decisions were made.
- The staged plan, review feedback, and scope corrections are part of the deliverable quality.
- For this take-home, demonstrating disciplined AI-assisted workflow is useful evidence of engineering judgment.
