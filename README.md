# liine-takehome

Container-first implementation for the Liine restaurant-hours take-home.

The app ingests `restaurants.csv` into SQLite with an ETL command and exposes `GET /restaurants/open?datetime=...` to answer which restaurants are open at a given local datetime.

## Reviewer Workflow

The host only needs Docker and `make`.

```bash
make build
make etl
make run
curl "http://localhost:8000/restaurants/open?datetime=2026-05-04T11:30:00"
```

Other useful commands:

```bash
make test
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

## API Contract

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
Availability uses local wall-clock weekly intervals with `[start, end)` semantics, so arrival at the opening minute is open and arrival at the closing minute is closed.

## Data Flow

- `make etl` reads `restaurants.csv`, parses schedule text, validates and normalizes intervals, and loads the runtime SQLite database
- `make run` starts the API against that same mounted runtime database
- API startup creates the schema if needed, but ETL is still required to populate restaurant data

## Testing And Verification

- `make lint` is the full verification pass: formatting checks, import-order checks, mypy, and pytest
- `make test` is available when you only want the test suite
- integration coverage includes ETL and API behavior, including overlap rejection and week-wrap handling

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
- Local wall-clock time only; no timezone-aware scheduling or conversions
- API datetime input is intentionally strict and ISO-like rather than natural-language parsed
