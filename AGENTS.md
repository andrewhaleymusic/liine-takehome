# AGENTS.md

## Purpose

This repo implements a container-first take-home assignment in deliberate stages. Prompts 1 through 3 are complete enough to provide project structure, persistence, and ETL behavior. The main remaining staged work is the availability API/query layer in Prompt 4.

## Working Rules

- Treat `assignment.md` and `restaurants.csv` as the source of truth.
- Keep all tooling inside Docker.
- Prefer small, explicit modules over clever abstractions.
- Correctness and reviewer clarity matter more than optimization.
- Keep parser, normalization, validation, and query concerns separate.
- Fail clearly when a required later-stage behavior is not implemented.

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

## Layout

- `app/api`: HTTP routes
- `app/core`: settings and logging
- `app/db`: DB setup helpers
- `app/etl`: CSV parsing and load pipeline
- `app/services`: domain logic
- `app/schemas`: Pydantic models
- `tests/unit`: fast unit tests
- `tests/integration`: broader integration coverage

## Expectations For Future Changes

- Prompt 4 should add the real availability endpoint and query logic against stored minute-of-week intervals.
- Preserve the current ETL behavior:
  - row-level failure logging
  - non-fatal bad-row handling
  - replace-per-restaurant writes
  - optional `etl --truncate`
- Keep the API simple unless a later requirement forces complexity.
