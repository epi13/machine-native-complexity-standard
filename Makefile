.PHONY: format lint type test build examples corpus mncds-corpus interoperability docs check

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

mncds-corpus:
	PYTHONPATH=src python scripts/run-mncds-corpus

interoperability:
	PYTHONPATH=src ./scripts/run-interoperability

docs:
	./scripts/build-docs

check: lint type test build examples corpus mncds-corpus interoperability docs
