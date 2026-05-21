.PHONY: install test lint format data data-live frontend frontend-dev clean

install:
	uv pip install -e ".[dev]"

install-sim:
	uv pip install -e ".[dev,sim]"

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

data:
	uv run bottom50-generate --output data/results.json
	cp data/results.json frontend/data/results.json

data-live:
	uv run bottom50-generate --live --output data/results.json --year 2026
	cp data/results.json frontend/data/results.json

frontend:
	cd frontend && bun install && bun run build

frontend-dev:
	cd frontend && bun run dev

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build
	rm -rf frontend/.next frontend/out
	find . -type d -name __pycache__ -exec rm -rf {} +
