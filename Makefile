IMAGE ?= stalen_cars:develop
CI_COMMIT_SHORT_SHA ?= $(shell git rev-parse --short HEAD)
GIT_STAMP ?= $(shell git describe)

.default: run

.EXPORT_ALL_VARIABLES:

run: COMPOSE ?= docker-compose -f compose-base.yaml -f compose-local.yaml
run: docker-build
	$(COMPOSE) up -d

stop: COMPOSE ?= docker-compose -f compose-base.yaml
stop:
	$(COMPOSE) stop

logs: COMPOSE ?= docker-compose -f compose-base.yaml
logs:
	$(COMPOSE) logs -f stolen-cars-api


celery-logs: COMPOSE ?= docker-compose -f compose-base.yaml
celery-logs:
	$(COMPOSE) logs -f celery

docker-build:
	docker build --build-arg version=$(GIT_STAMP) -t $(IMAGE) .
