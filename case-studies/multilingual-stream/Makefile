.PHONY: profiles providers generate c11 rust records experiment check clean

PYTHON ?= python3

profiles:
	PYTHONPATH=../../src ../../scripts/validate-language-profile ../../experimental/language-evidence/profiles/c11-reference-v0.1.json
	PYTHONPATH=../../src ../../scripts/validate-language-profile ../../experimental/language-evidence/profiles/rust-1.97.1-edition-2024-v0.1.json

providers:
	cd ../.. && ./scripts/run-language-provider-corpus

generate:
	$(PYTHON) generator/generate.py --check

c11:
	$(CC) -std=c11 -O2 -Wall -Wextra -Werror -pedantic c11/reference.c -o /tmp/mncs-stream-c-reference
	$(CC) -std=c11 -O2 -Wall -Wextra -Werror -pedantic c11/candidate.c -o /tmp/mncs-stream-c-candidate

rust:
	cargo fmt --check
	cargo clippy --locked --all-targets -- -D warnings
	cargo test --locked
	cargo build --release --locked

records:
	mncds validate mncds/development-record.json

experiment:
	$(PYTHON) tools/run_experiment.py --output /tmp/mncs-cross-language-report.json
	PYTHONPATH=../../src $(PYTHON) -c 'import json, pathlib; from mncs_validator.schemas import schema_errors; p=pathlib.Path("/tmp/mncs-cross-language-report.json"); errors=schema_errors(json.loads(p.read_text()), "cross-language-comparison"); assert not errors, errors'

check: profiles providers generate c11 rust records experiment

clean:
	rm -rf target /tmp/mncs-stream-c-reference /tmp/mncs-stream-c-candidate /tmp/mncs-cross-language-report.json
