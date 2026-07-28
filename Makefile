.PHONY: format lint type test build examples corpus mncds-corpus interoperability docs edgestream-smoke edgestream-evidence remote-water-smoke remote-water-test remote-water-study edgestream-water-integration cacheforge-smoke cacheforge-test cacheforge-study cacheforge-epoch2 ravel-test ravel-training-check ravel-unified-check dsense-check language-profile-schema language-provider-corpus multilingual-stream cacheforge-language-profile multilingual-wave-one go-profile go-provider-corpus go-gateway composed-gateway multilingual-wave-two composed-wave-three multilingual-wave-three composed-wave-four multilingual-wave-four check

WAVE_THREE_OUTPUT ?= evidence/actual
WAVE_FOUR_OUTPUT ?= evidence/actual

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
edgestream-water-integration:
	$(MAKE) -C case-studies/edgestream-remote-water-integration study
cacheforge-smoke:
	$(MAKE) -C case-studies/cacheforge smoke
cacheforge-test:
	$(MAKE) -C case-studies/cacheforge test
cacheforge-study:
	$(MAKE) -C case-studies/cacheforge study
cacheforge-epoch2:
	$(MAKE) -C case-studies/cacheforge epoch2
ravel-test:
	$(MAKE) -C case-studies/ravel test
ravel-training-check:
	$(MAKE) -C case-studies/ravel training-check
ravel-unified-check:
	$(MAKE) -C case-studies/ravel unified-check
dsense-check:
	$(MAKE) -C case-studies/dsense-desk-pet check
language-profile-schema:
	PYTHONPATH=src ./scripts/validate-language-profile experimental/language-evidence/profiles/c11-reference-v0.1.json
	PYTHONPATH=src ./scripts/validate-language-profile experimental/language-evidence/profiles/rust-1.97.1-edition-2024-v0.1.json
	PYTHONPATH=src ./scripts/validate-language-profile experimental/language-evidence/profiles/python-cpython-3.11-v0.1.json
language-provider-corpus:
	./scripts/run-language-provider-corpus
multilingual-stream:
	$(MAKE) -C case-studies/multilingual-stream check
cacheforge-language-profile:
	./scripts/verify-cacheforge-language-profile
multilingual-wave-one:
	./scripts/run-multilingual-wave-one
go-profile:
	PYTHONPATH=src ./scripts/validate-language-profile experimental/language-evidence/profiles/go-1.23-v0.2.json
go-provider-corpus:
	./scripts/run-wave-two-provider-corpus
go-gateway:
	$(MAKE) -C case-studies/go-gateway check
composed-gateway:
	$(MAKE) -C case-studies/composed-gateway check
multilingual-wave-two: go-profile go-provider-corpus
	PYTHONPATH=src ./scripts/verify-wave-two
	$(MAKE) go-gateway
	$(MAKE) composed-gateway
composed-wave-three:
	$(MAKE) -C case-studies/composed-gateway/wave-three OUTPUT=$(WAVE_THREE_OUTPUT) check
multilingual-wave-three: go-profile go-provider-corpus
	PYTHONPATH=src ./scripts/verify-wave-three
	$(MAKE) composed-wave-three WAVE_THREE_OUTPUT=$(WAVE_THREE_OUTPUT)
composed-wave-four:
	$(MAKE) -C case-studies/composed-gateway/wave-four OUTPUT=$(WAVE_FOUR_OUTPUT) check
multilingual-wave-four:
	PYTHONPATH=src ./scripts/verify-wave-four
	$(MAKE) composed-wave-four WAVE_FOUR_OUTPUT=$(WAVE_FOUR_OUTPUT)
check: lint type test build examples corpus mncds-corpus interoperability docs
