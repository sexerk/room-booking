.PHONY: help up down logs migrate test shell clean

help:
	@echo "Available commands:"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make logs      - Follow logs"
	@echo "  make migrate   - Run alembic migrations"
	@echo "  make test      - Run tests"
	@echo "  make shell     - Open shell in api container"
	@echo "  make clean     - Clean up docker volumes"

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

migrate:
	docker-compose exec api alembic upgrade head

test:
	docker-compose exec api pytest tests/ -v

shell:
	docker-compose exec api /bin/bash

clean:
	docker-compose down -v
	rm -rf .pytest_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +

alembic-init:
	docker-compose exec api alembic init app/db/migrations

alembic-migrate:
	docker-compose exec api alembic revision --autogenerate -m "$(m)"

alembic-upgrade:
	docker-compose exec api alembic upgrade head

alembic-downgrade:
	docker-compose exec api alembic downgrade -1