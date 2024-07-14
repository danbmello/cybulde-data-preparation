.PHONY: all entrypoint notebook sort sort-check format format-check format-and-sort lint check-type-annotations test full-check build build-for-dependencies lock-dependencies up down exec-in

SHELL = /usr/bin/env bash
USER_NAME = $(USERNAME)
USER_ID = 1000
HOST_NAME = $(COMPUTERNAME)

DOCKER_COMPOSE_COMMAND = docker-compose

SERVICE_NAME = app
CONTAINER_NAME = cybulde-data-processing-container

DIRS_TO_VALIDATE = cybulde
DOCKER_COMPOSE_RUN = $(DOCKER_COMPOSE_COMMAND) run --rm $(SERVICE_NAME)
DOCKER_COMPOSE_EXEC = $(DOCKER_COMPOSE_COMMAND) exec $(SERVICE_NAME)

# Local docker image name
LOCAL_DOCKER_IMAGE_NAME = cybulde-data-processing

# Docker image name
GCP_DOCKER_IMAGE_NAME = southamerica-east1-docker.pkg.dev/cybulde-428517/cybulde/cybulde-data-processing

# Create random image tag
# The ":=" fix the value of GCP_DOKER_IMAGE_TAG, it won't change on different runs.
# GCP_DOCKER_IMAGE_TAG := $(shell powershell -Command "[guid]::NewGuid().ToString()")
GCP_DOCKER_IMAGE_TAG := $(strip $(shell powershell -Command "[guid]::NewGuid().ToString()"))


export

# Returns true if the stem is a non-empty environment variable, or else raises an error.
guard-%:
	@echo off && \
	setlocal enabledelayedexpansion && \
	set VAR_NAME=$* && \
	set VAR_VALUE=!%VAR_NAME%! && \
	if "!VAR_VALUE!"=="" ( \
	    echo $* is not set && \
	    exit /b 1) && \
	exit /b 0

## Generate final config. CONFIG_NAME=<config_name> has to be providded. For overrides use: OVERRIDES=<overrides>
generate-final-config: up guard-CONFIG_NAME
	$(DOCKER_COMPOSE_EXEC) python ./cybulde/generate_final_config.py --config-name ${CONFIG_NAME} --overrides docker_image_name=$(GCP_DOCKER_IMAGE_NAME) docker_image_tag=$(GCP_DOCKER_IMAGE_TAG) ${OVERRIDES}

## Generate final data processing config. For overrides use: OVERRIDES=<overrides>
generate-final-data-processing-config: up
	$(DOCKER_COMPOSE_EXEC) python ./cybulde/generate_final_config.py --config-name data_processing_config --overrides docker_image_name=$(GCP_DOCKER_IMAGE_NAME) docker_image_tag=$(GCP_DOCKER_IMAGE_TAG) ${OVERRIDES}

## Process raw data
process-data: generate-final-data-processing-config push
	$(DOCKER_COMPOSE_EXEC) python ./cybulde/process_data.py

## Processes raw data without pushing docker image to GCP
local-process-data: generate-final-data-processing-config
	$(DOCKER_COMPOSE_EXEC) python ./cybulde/process_data.py

## Push docker image to GCP artifact registery
push: build
	gcloud auth configure-docker --quiet europe-west4-docker.pkg.dev
	docker tag $(LOCAL_DOCKER_IMAGE_NAME):latest "$(GCP_DOCKER_IMAGE_NAME):$(GCP_DOCKER_IMAGE_TAG)"
	docker push "$(GCP_DOCKER_IMAGE_NAME):$(GCP_DOCKER_IMAGE_TAG)"

## Starts jupyter lab
notebook: up
	$(DOCKER_COMPOSE_EXEC) jupyter-lab --ip 0.0.0.0 --port 8888 --no-browser

## Sort code using isort
sort: up
	$(DOCKER_COMPOSE_EXEC) isort --atomic $(DIRS_TO_VALIDATE)

## Check sorting using isort
sort-check: up
	$(DOCKER_COMPOSE_EXEC) isort --check-only --atomic $(DIRS_TO_VALIDATE)

## Format code using black
format: up
	$(DOCKER_COMPOSE_EXEC) black $(DIRS_TO_VALIDATE)

## Check format using black
format-check: up
	$(DOCKER_COMPOSE_EXEC) black --check $(DIRS_TO_VALIDATE)

## Format and sort code using black and isort
format-and-sort: sort format

## Lint code using flake8
lint: up format-check sort-check
	$(DOCKER_COMPOSE_EXEC) flake8 $(DIRS_TO_VALIDATE)

## Check type annotations using mypy
check-type-annotations: up
	$(DOCKER_COMPOSE_EXEC) mypy $(DIRS_TO_VALIDATE)

## Run tests with pytest
test: up
	$(DOCKER_COMPOSE_EXEC) pytest

## Perform a full check
full-check: lint check-type-annotations
	$(DOCKER_COMPOSE_EXEC) pytest --cov --cov-report xml --verbose

## Builds docker image
build:
	$(DOCKER_COMPOSE_COMMAND) build $(SERVICE_NAME)

## Builds docker image no cache
build-no-cache:
	$(DOCKER_COMPOSE_COMMAND) build $(SERVICE_NAME) --no-cache

## Remove poetry.lock and build docker image
build-for-dependencies:
	powershell -Command "Remove-Item -Force *.lock"
	$(DOCKER_COMPOSE_COMMAND) build $(SERVICE_NAME)

## Lock dependencies with poetry
lock-dependencies: build-for-dependencies
	$(DOCKER_COMPOSE_RUN) bash -c "if [ -e /home/$(USER_NAME)/poetry.lock.build ]; then cp /home/$(USER_NAME)/poetry.lock.build ./poetry.lock; else poetry lock; fi"

## Starts docker containers using "docker-compose up -d"
up:
	$(DOCKER_COMPOSE_COMMAND) up -d

## docker-compose down
down:
	$(DOCKER_COMPOSE_COMMAND) down

## Open an interactive shell in docker container
exec-in: up
	docker exec -it $(CONTAINER_NAME) bash

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@powershell -Command "Write-Output 'Available rules:'; \
	Get-Content ${MAKEFILE_LIST} | ForEach-Object { \
		if ($$_ -match '^## (.+)') { \
			$$description = $$matches[1] \
		} elseif ($$_ -match '^([a-zA-Z0-9_-]+):') { \
			$$target = $$matches[1]; \
			Write-Host -ForegroundColor Cyan $$target -NoNewline; \
			Write-Host ': ' -NoNewline; \
			Write-Host $$description \
		} \
	}"