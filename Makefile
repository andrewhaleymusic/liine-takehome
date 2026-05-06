IMAGE := liine-takehome
PORT := 8000
DATA_DIR := $(CURDIR)/.docker-data
DOCKER_UID := $(shell id -u)
DOCKER_GID := $(shell id -g)
MOUNTED_APP_RUN := docker run --rm --user $(DOCKER_UID):$(DOCKER_GID) -e HOME=/tmp -e XDG_CACHE_HOME=/tmp/.cache -e MYPY_CACHE_DIR=/tmp/.mypy_cache -e PYTEST_ADDOPTS=-p\ no:cacheprovider -v $(CURDIR):/app -w /app $(IMAGE)

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
	docker run --rm -it -v $(DATA_DIR):/data --entrypoint sh $(IMAGE)

fmt: build
	$(MOUNTED_APP_RUN) fmt

lint: build
	$(MOUNTED_APP_RUN) lint

clean:
	rm -rf $(DATA_DIR)
