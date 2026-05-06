# liine-takehome

Container-first scaffold for the Liine restaurant-hours take-home.

This repo currently implements Prompt 1 and the storage-focused parts of Prompt 2:

- project structure
- Docker and Makefile workflow
- app configuration
- CLI entrypoints
- a stub FastAPI app
- basic smoke-test wiring
- Prompt 2 schema and stored-interval domain primitives

The CSV parser, ETL load flow, and availability endpoint are intentionally deferred to later prompts.

## Reviewer Workflow

The host only needs Docker and `make`.

```bash
make build
make test
make run
```

Other useful commands:

```bash
make etl
make fmt
make lint
make shell
```

## Command Behavior

- `make run` starts the FastAPI container on port `8000`
- `make test` runs the pytest suite in the container
- `make fmt` runs `isort` and `black` against the local working tree through the container
- `make lint` runs `black --check`, `isort --check-only`, `mypy`, and `pytest`
- `make etl` is wired up but intentionally returns a not-implemented error until Prompt 3

The runtime sqlite database is expected at `/data/restaurants.db` inside the container and is backed by the host directory `.docker-data/`.

## Current API Surface

The scaffold currently exposes one endpoint:

- `GET /health`

Example:

```bash
curl http://localhost:8000/health
```

## Configuration

Configuration is environment-driven through `LIINE_`-prefixed variables.

- `LIINE_DATABASE_URL`
- `LIINE_TEST_DATABASE_URL`
- `LIINE_CSV_PATH`
- `LIINE_API_HOST`
- `LIINE_API_PORT`
- `LIINE_LOG_LEVEL`

Defaults are set for local container use and isolated test DB wiring.

## Intentional Tradeoffs

- No migration framework yet
- No production hardening beyond what is useful for the take-home
- No CSV parsing or row-level ETL orchestration yet
- No automatic ETL on app startup; the app should fail clearly if runtime data is missing once the real endpoint exists
