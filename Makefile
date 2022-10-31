.PHONY: up down shell migrate_head migrate_base

DOCKER_TAG := latest
up: ## do docker compose up with hot release
	docker compose up

down: ## do docker compose down
	docker compose down

ps: ## check container status
	docker compose ps

shell: ## login api shell
	docker exec -it api /bin/sh

migrate_head:
	docker compose run --rm api alembic upgrade head

migrate_base:
	docker compose --rm api alembic downgrade base

# test: ## execute tests
# 	go test -v ./...
