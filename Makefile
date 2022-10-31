.PHONY: up down build bash head base

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

# test: ## execute tests
# 	go test -v ./...
