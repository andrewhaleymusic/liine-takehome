# liine-takehome

Container-first implementation for the Liine restaurant-hours take-home.

This repo currently implements:

- project structure
- Docker and Makefile workflow
- app configuration
- CLI entrypoints
- FastAPI API surface
- Prompt 2 schema and stored-interval domain primitives
- Prompt 3 ETL parsing, normalization, validation, and load flow
- Prompt 4 availability query endpoint

The app answers "which restaurants are open at this local datetime?" using ETL-loaded sqlite data.

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
- `make etl` parses `restaurants.csv` and loads the runtime sqlite database
- the container entrypoint also supports `etl --truncate` for a clean reload before ingesting data

The runtime sqlite database is expected at `/data/restaurants.db` inside the container and is backed by the host directory `.docker-data/`.

## Current API Surface

The app currently exposes:

- `GET /health`
- `GET /restaurants/open?datetime=...`

Example:

```bash
curl http://localhost:8000/health
```

```bash
curl "http://localhost:8000/restaurants/open?datetime=2026-05-04T11:30:00"
```

`/restaurants/open` expects a naive local datetime string. The documented format is ISO-like local datetime, for example `2026-05-04T11:30:00`.
The response echoes that value as the string field `requested_datetime`.

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
- No automatic ETL on app startup; the API creates the schema on startup, but an empty runtime DB simply returns no open restaurants until `make etl` loads data
