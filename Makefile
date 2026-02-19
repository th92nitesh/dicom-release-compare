.PHONY: install dev-up dev-down doctor pipeline init-run test lint

install:
	python -m pip install -e .[dev]

dev-up:
	docker compose up -d

dev-down:
	docker compose down -v

doctor:
	drc doctor

pipeline:
	drc pipeline

init-run:
	drc init-run 2024e 2026a

test:
	pytest -q

lint:
	ruff check src tests
