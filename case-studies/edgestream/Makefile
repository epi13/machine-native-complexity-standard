.PHONY: generate build test benchmark evidence validate smoke clean

generate:
	python tools/run_study.py generate

build: generate
	python tools/run_study.py build

test: build
	python tools/run_study.py test

benchmark: build
	python tools/run_study.py benchmark

evidence:
	python tools/run_study.py all
	python tools/package_evidence.py

validate:
	mncs validate-bundle . --require-pass
	mncds validate mncds/development-record.json --require-pass

smoke:
	python tools/smoke.py
	python tools/package_evidence.py
	mncs validate-bundle . --require-pass
	mncds validate mncds/development-record.json --require-pass

clean:
	rm -rf build
	rm -f workloads/*.bin
