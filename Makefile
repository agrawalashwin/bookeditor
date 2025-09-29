.PHONY: dev api web migrate test

dev:
	@echo "Run API and Web locally with two terminals"
	@echo "cd api && poetry run uvicorn app.main:app --reload --port 8000"
	@echo "cd web && npm run dev"

api:
	cd api && poetry run uvicorn app.main:app --reload --port 8000

web:
	cd web && npm run dev

migrate:
	@echo "Run Alembic migrations (implement in api)"

test:
	@echo "Run tests (implement)"
