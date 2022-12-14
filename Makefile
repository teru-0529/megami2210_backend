.PHONY: up down build bash head base test

DOCKER_TAG := latest
up: ## do docker compose up with hot release
	docker compose up

down: ## do docker compose down
	docker compose down

build:
	docker compose build

bash: ## login api shell
	docker exec -it api bash

head:
	docker exec -it api alembic upgrade head

base:
	docker exec -it api alembic downgrade base

test: ## execute tests
	docker-compose run --rm --entrypoint "poetry run pytest -vv --cov=app --cov-report=html" api

test_ok: ## execute tests
	docker-compose run --rm --entrypoint "poetry run pytest -m "ok" -vv" api

test_ng: ## execute tests
	docker-compose run --rm --entrypoint "poetry run pytest -m "ng" -vv" api

test_product: ## execute tests
	docker-compose run --rm --entrypoint "poetry run pytest -m "product" -vv" api
