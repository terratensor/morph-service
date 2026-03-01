.PHONY: help build up down logs test clean

help:
	@echo "Available commands:"
	@echo "  make build    - Build Docker images"
	@echo "  make up       - Start services"
	@echo "  make down     - Stop services"
	@echo "  make logs     - View logs"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up"

build:
	docker compose build

up:
	docker compose up -d
	@echo "Service is running at http://localhost:8000"
	@echo "Redis Commander at http://localhost:8081 (dev mode)"

down:
	docker compose down

logs:
	docker compose logs -f

test:
	pytest tests/ -v --cov=app

clean:
	docker compose down -v
	docker system prune -f

prod-up:
	ENV=production docker compose up -d

dev-up:
	ENV=development docker compose --profile dev up -d