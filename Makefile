.PHONY: format lint type test build examples corpus mncds-corpus interoperability docs edgestream-smoke edgestream-evidence remote-water-smoke remote-water-test remote-water-study check

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

edgestream-smoke:
	$(MAKE) -C case-studies/edgestream smoke

edgestream-evidence:
	$(MAKE) -C case-studies/edgestream evidence

remote-water-smoke:
	$(MAKE) -C case-studies/remote-water-control smoke

remote-water-test:
	$(MAKE) -C case-studies/remote-water-control test

remote-water-study:
	$(MAKE) -C case-studies/remote-water-control study

check: lint type test build examples corpus mncds-corpus interoperability docs
