# AGENTS.md

## Purpose

This repo implements a container-first take-home assignment with a complete ETL-to-API flow. The app loads restaurant hours from `restaurants.csv` into SQLite and answers availability queries through a FastAPI endpoint.

## Working Rules

- Treat `assignment.md` and `restaurants.csv` as the source of truth.
- Keep all tooling inside Docker.
- Prefer small, explicit modules over clever abstractions.
- Correctness and reviewer clarity matter more than optimization.
- Keep parser, normalization, validation, and query concerns separate.
- Keep docs aligned with actual runtime behavior; remove stale prompt-stage references when implementation catches up.

## Command Surface

The container entrypoint is `liine`, with these subcommands:

- `serve`
- `etl`
- `test`
- `fmt`
- `lint`

The Makefile is the primary reviewer interface.

Use these targets instead of invoking host tools directly:

- `make build`: build the Docker image
- `make test`: run the pytest suite in Docker
- `make lint`: run `black --check`, `isort --check-only`, `mypy`, and `pytest` in Docker
- `make fmt`: run `isort` and `black` against the mounted working tree through Docker
- `make etl`: load `restaurants.csv` into the runtime sqlite database
- `make run`: start the API container
- `make shell`: open a shell in the container

Do not run bare host commands like `pytest`, `black`, `isort`, or `mypy` for verification unless there is a repo-specific reason the Makefile cannot be used. For review workflows, prefer `make lint` first, then `make test` only if you need a narrower rerun.

Recommended reviewer flow:

- `make build`
- `make etl`
- `make run`
- `curl "http://localhost:8000/restaurants/open?datetime=2026-05-04T11:30:00"`
- `make lint`

## Layout

- `app/api`: HTTP routes
- `app/core`: settings and logging
- `app/db`: DB setup helpers
- `app/etl`: CSV parsing and load pipeline
- `app/services`: domain logic
- `app/schemas`: Pydantic models
- `tests/unit`: fast unit tests
- `tests/integration`: broader integration coverage

## Key Invariants

- Store restaurant availability as normalized minute-of-week intervals.
- Use `[start, end)` semantics for open intervals.
- Do not allow overlapping intervals for the same restaurant.
- Keep runtime behavior in local wall-clock time only.
- The API accepts a naive local datetime string and returns restaurant names sorted alphabetically.

## Expectations For Future Changes

- Preserve the current ETL behavior:
  - row-level failure logging
  - non-fatal bad-row handling
  - replace-per-restaurant writes
  - optional `etl --truncate`
- Keep schema creation at application/command startup boundaries, not inside request handlers or low-level loader helpers.
- Keep the API simple unless a later requirement forces complexity.
