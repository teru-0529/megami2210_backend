.PHONY: up down bash head base

DOCKER_TAG := latest
up: ## do docker compose up with hot release
	docker compose up

down: ## do docker compose down
	docker compose down

bash: ## login api shell
	docker exec -it api bash

head:
	docker compose run --rm api alembic upgrade head

base:
	docker compose --rm api alembic downgrade base

# test: ## execute tests
# 	go test -v ./...
