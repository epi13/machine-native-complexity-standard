.PHONY: format lint type test build examples corpus mncds-corpus interoperability release-candidate-schema release-candidate-corpus release-candidate-independent release-candidate-check docs family check

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
release-candidate-schema:
	PYTHONPATH=src python -c "from mncs_validator.schemas import load_schema; [load_schema(name) for name in ('contract-profile-0.3','assurance-case-0.3','threat-record-0.3','measurement-profile-0.3','mncds-development-record-0.1')]"
release-candidate-corpus:
	PYTHONPATH=src ./scripts/run-release-candidate-corpus
release-candidate-independent:
	cargo test --manifest-path independent/rc-consumer/Cargo.toml
	cargo clippy --manifest-path independent/rc-consumer/Cargo.toml --all-targets -- -D warnings
	PYTHONPATH=src ./scripts/compare-release-candidate-consumers
release-candidate-check: release-candidate-schema release-candidate-corpus release-candidate-independent
docs:
	./scripts/build-docs
family:
	PYTHONPATH=src python scripts/validate-family-registry.py
	PYTHONPATH=src python -c "from mncs_validator.cli import main; raise SystemExit(main(['family','--json']))"
check: lint type test build examples corpus mncds-corpus interoperability release-candidate-check family docs
