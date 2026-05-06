IMAGE := liine-takehome
ENV_FILE := .env
include $(ENV_FILE)

DATA_DIR := $(CURDIR)/.docker-data
CSV_MOUNT_PATH := /tmp/input.csv
DOCKER_UID := $(shell id -u)
DOCKER_GID := $(shell id -g)
MOUNTED_APP_RUN := docker run --rm --user $(DOCKER_UID):$(DOCKER_GID) -e HOME=/tmp -e XDG_CACHE_HOME=/tmp/.cache -e MYPY_CACHE_DIR=/tmp/.mypy_cache -e PYTEST_ADDOPTS=-p\ no:cacheprovider -v $(CURDIR):/app -w /app $(IMAGE)

.PHONY: build test etl etl-truncate run shell fmt lint clean

build:
	docker build -t $(IMAGE) .

test: build
	docker run --rm $(IMAGE) test

etl: build
	mkdir -p $(DATA_DIR)
	docker run --rm --env-file $(ENV_FILE) -v $(DATA_DIR):/data -v $(abspath $(LIINE_CSV_PATH)):$(CSV_MOUNT_PATH):ro -e LIINE_CSV_PATH=$(CSV_MOUNT_PATH) $(IMAGE) etl

etl-truncate: build
	mkdir -p $(DATA_DIR)
	docker run --rm --env-file $(ENV_FILE) -v $(DATA_DIR):/data -v $(abspath $(LIINE_CSV_PATH)):$(CSV_MOUNT_PATH):ro -e LIINE_CSV_PATH=$(CSV_MOUNT_PATH) $(IMAGE) etl --truncate

run: build
	mkdir -p $(DATA_DIR)
	docker run --rm --env-file $(ENV_FILE) -p 127.0.0.1:$(LIINE_API_PORT):$(LIINE_API_PORT) -v $(DATA_DIR):/data $(IMAGE) serve

shell: build
	mkdir -p $(DATA_DIR)
	docker run --rm -it --env-file $(ENV_FILE) -v $(DATA_DIR):/data -v $(abspath $(LIINE_CSV_PATH)):$(CSV_MOUNT_PATH):ro -e LIINE_CSV_PATH=$(CSV_MOUNT_PATH) --entrypoint sh $(IMAGE)

fmt: build
	$(MOUNTED_APP_RUN) fmt

lint: build
	$(MOUNTED_APP_RUN) lint

clean:
	rm -rf $(DATA_DIR)
