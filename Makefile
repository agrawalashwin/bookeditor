.PHONY: dev api web migrate test seed install docker-up docker-down

install:
	@echo "Installing dependencies..."
	cd api && export PATH="$$HOME/.local/bin:$$PATH" && poetry install
	cd web && npm install

docker-up:
	docker-compose up postgres -d
	@echo "Waiting for PostgreSQL to be ready..."
	sleep 5

docker-down:
	docker-compose down

seed:
	cd api && export PATH="$$HOME/.local/bin:$$PATH" && python seed.py

dev:
	@echo "Starting development servers..."
	@echo "API: http://localhost:8000"
	@echo "Web: http://localhost:3000"
	@echo ""
	@echo "Run in separate terminals:"
	@echo "  make api"
	@echo "  make web"

api:
	cd api && export PATH="$$HOME/.local/bin:$$PATH" && poetry run uvicorn app.main:app --reload --port 8000

web:
	cd web && npm run dev

migrate:
	cd api && export PATH="$$HOME/.local/bin:$$PATH" && poetry run alembic upgrade head

test:
	cd api && export PATH="$$HOME/.local/bin:$$PATH" && poetry run pytest
	cd web && npm test

setup: install docker-up migrate seed
	@echo "Setup complete! Run 'make dev' to start development servers."
