.PHONY: format lint type test build examples docs check

format:
	ruff format .

lint:
	ruff format --check .
	ruff check .

type:
	mypy src

test:
	pytest

build:
	python -m build

examples:
	./scripts/verify-examples

docs:
	./scripts/build-docs

check: lint type test build examples docs
