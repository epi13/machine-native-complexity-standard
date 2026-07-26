.PHONY: format lint type test build examples corpus interoperability docs check

format:
	ruff format .

lint:
	ruff format --check .
	ruff check .

type:
	mypy src

test:
	PYTHONPATH=src pytest

build:
	python -m build

examples:
	PYTHONPATH=src ./scripts/verify-examples

corpus:
	PYTHONPATH=src ./scripts/run-conformance-corpus

interoperability:
	PYTHONPATH=src ./scripts/run-interoperability

docs:
	./scripts/build-docs

check: lint type test build examples corpus interoperability docs
