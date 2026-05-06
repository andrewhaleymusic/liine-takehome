# liine-takehome

Container-first implementation for the Liine restaurant-hours take-home.

The app ingests `restaurants.csv` into SQLite with an ETL command and exposes `GET /restaurants/open?datetime=...` to answer which restaurants are open at a given local datetime.

## AI Workflow Note

This repo intentionally includes `prompt.md` and `work_journal.md`.

- `prompt.md` shows how the take-home was broken into small, scoped planning and implementation steps instead of being one-shotted.
- `work_journal.md` records the decisions, tradeoffs, review feedback, and exploratory testing notes that came out of that process.

They are included to be transparent about an AI-assisted local development workflow and to show how the work was scoped, validated, and refined over time.

## Reviewer Workflow

The host only needs Docker, `curl`, and `make`.

```bash
make build
make etl
make run
curl "http://localhost:8000/restaurants/open?datetime=2026-05-04T11:30:00"
```

Other useful commands:

```bash
make test
make etl-truncate
make fmt
make lint
make shell
```

## Command Behavior

- `make run` starts the FastAPI container on the port configured by `LIINE_API_PORT` in `.env` (`8000` by default)
- `make test` runs the pytest suite in the container
- `make fmt` runs `isort` and `black` against the local working tree through the container
- `make lint` runs `black --check`, `isort --check-only`, `mypy`, and `pytest`
- `make etl` parses the CSV pointed to by `LIINE_CSV_PATH` in `.env` and loads the runtime sqlite database
- `make etl-truncate` does a clean reload before ingesting data

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
Accepted examples include:

- `2026-05-04T11:30:00`
- `2026-05-04T11:30`
- `2026-05-04 11:30:00`

Rejected examples include:

- `2026-05-04T11:30:00.123`
- `2026-05-04T11:30:00Z`
- `2026-05-04T11:30:00-04:00`

The response echoes that value as the string field `requested_datetime`.
Availability uses local wall-clock weekly intervals with `[start, end)` semantics, so arrival at the opening minute is open and arrival at the closing minute is closed.

## Data Flow

- `make etl` reads the CSV configured in `.env`, parses schedule text, validates and normalizes intervals, and loads the runtime SQLite database
- `make run` starts the API against that same mounted runtime database
- API startup creates the schema if needed, but ETL is still required to populate restaurant data

## Testing And Verification

- `make lint` is the full verification pass: formatting checks, import-order checks, mypy, and pytest
- `make test` is available when you only want the test suite
- integration coverage includes ETL and API behavior, including overlap rejection and week-wrap handling

## Configuration

The reviewer workflow uses the committed `.env` file as the supported runtime configuration surface.

The default `.env` includes:

- `LIINE_DATABASE_URL`
- `LIINE_TEST_DATABASE_URL`
- `LIINE_CSV_PATH`
- `LIINE_API_HOST`
- `LIINE_API_PORT`
- `LIINE_LOG_LEVEL`

If you want to change the runtime DB path, API port, log level, or input CSV, edit `.env` and then rerun the relevant `make` target.

Examples:

```bash
# point ETL at a different source file, then reload
vim .env
make etl

# clear runtime data and reload using the current .env settings
make etl-truncate
```

`LIINE_CSV_PATH` in `.env` is a host path used by the Makefile for the ETL bind mount. The Makefile rewrites it to an in-container path before running `liine etl`.

## Intentional Tradeoffs

- No migration framework yet
- No production hardening beyond what is useful for the take-home
- No automatic ETL on app startup; the API creates the schema on startup, but an empty runtime DB simply returns no open restaurants until `make etl` loads data
- Local wall-clock time only; no timezone-aware scheduling or conversions
- API datetime input is intentionally strict and ISO-like rather than natural-language parsed
