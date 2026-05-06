# AGENTS.md

## Purpose

This repo implements a container-first take-home assignment in deliberate stages. Prompt 1 owns project structure and operational scaffolding only. Do not prematurely lock in schedule parsing, persistence rules, or query semantics before their dedicated planning steps.

## Working Rules

- Treat `assignment.md` and `restaurants.csv` as the source of truth.
- Keep all tooling inside Docker.
- Prefer small, explicit modules over clever abstractions.
- Correctness and reviewer clarity matter more than optimization.
- Fail clearly when a required later-stage behavior is not implemented.

## Command Surface

The container entrypoint is `liine`, with these subcommands:

- `serve`
- `etl`
- `test`
- `fmt`
- `lint`

The Makefile is the primary reviewer interface.

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

- Prompt 2 should define the sqlite schema and interval invariants.
- Prompt 3 should implement ETL with row-level failure logging and non-fatal bad-row handling.
- Prompt 4 should add the real availability endpoint and query logic.
- Keep the API simple unless a later requirement forces complexity.
