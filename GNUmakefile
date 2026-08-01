# Current development entry points. The included Makefile remains byte-for-byte
# frozen because it is authority bound by the historical RAVEL 0.5 manifest.
include Makefile

.PHONY: core-check core-test forge-integration-test ravel-0.6-preregistration-check

core-test:
	PYTHONPATH=src pytest -m "not experimental"

core-check: lint type core-test build examples corpus mncds-corpus interoperability release-candidate-check docs

forge-integration-test:
	PYTHONPATH=src pytest -q tests/test_forge_integration.py

ravel-0.6-preregistration-check:
	PYTHONPATH=src pytest -q tests/test_ravel_0_6_preregistration.py
