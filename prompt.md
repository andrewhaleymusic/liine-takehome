I am working on a take-home exercise for a job interview. The assignment text is in `assignment.md`, and the source data is in `restaurants.csv`.

I do not want to one-shot the assignment with a strong model. I want to break the work into small, explicit steps and use a separate `/plan` session for each step. Please stay within the scope of the current step, explain tradeoffs, and wait for confirmation before moving on to the next one.

Use the local files in this repo as the source of truth. Do not refer to an external gist.

## Shared Constraints

- Assume the evaluator has a reasonably recent Docker installation and can run `make`.
- Do not assume the evaluator has Python, uv, sqlite, pytest, mypy, black, isort, or any other tooling installed on the host.
- All app code, tests, scripts, linting, and formatting must run inside the container.
- The REST API must be reachable from outside the container with `curl` or another HTTP client.
- Use Python for the implementation.
- Use sqlite, FastAPI, SQLAlchemy, Pydantic, pytest, and uv.
- `make lint` should run mypy, black, and isort in check mode.
- `make fmt` should run black and isort in fix mode.
- We do not need pre-commit hooks.
- The sqlite database should live on a mounted Docker volume or bind mount so data written during ETL is still present when the API container starts.
- The assignment says to treat times as local and to ignore timezone-awareness. Keep restaurant hours in local wall-clock time. Do not convert recurring weekly hours to UTC.
- Use separate sqlite databases for app/runtime data and test data, even if they share the same schema.
- I do not care about adding a migration framework unless there is a very strong reason.

The reviewer workflow should look roughly like this pseudocode:

```make
IMAGE := liine-takehome
PORT := 8000
DATA_DIR := $(CURDIR)/.docker-data

.PHONY: build test etl run shell fmt lint clean

build:
	docker build -t $(IMAGE) .

test: build
	docker run --rm $(IMAGE) test

etl: build
	mkdir -p $(DATA_DIR)
	docker run --rm -v $(DATA_DIR):/data $(IMAGE) etl

run: build
	mkdir -p $(DATA_DIR)
	docker run --rm -p $(PORT):8000 -v $(DATA_DIR):/data $(IMAGE) serve

shell: build
	mkdir -p $(DATA_DIR)
	docker run --rm -it -v $(DATA_DIR):/data $(IMAGE) sh

fmt: build
	docker run --rm $(IMAGE) fmt

lint: build
	docker run --rm $(IMAGE) lint

clean:
	rm -rf $(DATA_DIR)
```

## Prompt 1: Architecture And Repo Shape

Please review `assignment.md` and propose the architecture for this take-home.

Scope for this step:

- Recommend the repo structure.
- Recommend the Dockerfile and Makefile responsibilities.
- Recommend how commands like `test`, `etl`, `serve`, `fmt`, and `lint` should be exposed inside the container.
- Recommend how app config should distinguish runtime DB vs test DB.
- Recommend whether `README.md` and `AGENTS.md` should be created now and what they should contain.

Constraints for your answer:

- Do not write code yet unless it is necessary to illustrate a structure.
- Be explicit about assumptions and tradeoffs.
- Call out anything in the assignment that is underspecified and propose a concrete default.

## Prompt 2: Data Model And Schedule Semantics

Please design the persistence model for restaurant hours based on `assignment.md` and `restaurants.csv`.

Current inclination:

```text
restaurants
- restaurant_id uuid primary key
- name varchar(255)

open_blocks
- open_block_id uuid primary key
- restaurant_id uuid foreign key
- start_dow int    -- 0-6
- start_time time
- end_dow int      -- 0-6
- end_time time
```

Important business rules:

- We need to support hours that cross midnight, for example Sunday 5:00 PM to Monday 3:00 AM.
- Store times as local wall-clock values, not UTC.
- Open intervals should use `[start, end)` semantics.
- If a restaurant opens at 11:00 and a customer shows up at 11:00, that counts as open.
- If a restaurant closes at 11:00 and a customer shows up at 11:00, that counts as closed.
- Overlapping open blocks for the same restaurant should not be allowed.

Scope for this step:

- Critically review this schema.
- Suggest better names if appropriate.
- Define validation and normalization rules.
- Identify edge cases from `restaurants.csv` that the schema must support.
- Explain how you would enforce non-overlap.

Constraints for your answer:

- Stay focused on data modeling and invariants.
- Do not jump ahead to API implementation.
- If you think two tables are not sufficient, make the case clearly.

## Prompt 3: ETL Plan

Please design the ETL flow that will read `restaurants.csv`, parse the human-readable schedule strings, validate them, and load sqlite.
    

Scope for this step:

- Break the ETL process into stages.
- Identify parser edge cases and failure modes.
- Recommend where validation should live.
- Explain how to make ETL idempotent for local development.
- Explain how tests should cover parsing and data loading.

Constraints for your answer:

- Prefer a simple, maintainable implementation over a clever one.
- Avoid regex, prefer raw string processing for easier debugging.
- Tie the plan back to the data model decisions from Prompt 2.
- Any failure should be logged such that a human can see which row failed and the text that caused the failure.


## Prompt 4: API And Tests

Please propose the API contract and testing strategy for the take-home described in `assignment.md`.

Scope for this step:

- Define the request and response shape for the endpoint.
- Explain how datetime parsing should behave.
- Explain how to query for restaurants open at a given local datetime.
- Define the minimum test suite needed for confidence.
- Call out any integration tests that should run against the containerized app.

Constraints for your answer:

- Keep the API simple unless the assignment requires more.
- Favor correctness and clarity over premature optimization.

## Prompt 5: Documentation And Delivery

Please propose the final documentation and delivery checklist for this repo.

Scope for this step:

- Recommend the contents of `README.md`.
- Recommend the contents of `AGENTS.md`.
- Recommend what commands the reviewer should run first.
- Recommend what tradeoffs or future improvements should be documented explicitly.

Constraints for your answer:

- Focus on reviewer experience.
- Keep the deliverable modest and credible for a take-home assignment.
