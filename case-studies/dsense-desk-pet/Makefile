.PHONY: test evidence materialize check clean

PYTHON ?= python3

# Offline mechanism, identity, and evidence checks. This does not replace AVR compilation.
test:
	$(PYTHON) tools/verify_case_study.py

evidence:
	$(PYTHON) tools/analyze_epoch1.py

materialize:
	$(PYTHON) tools/materialize.py

check:
	$(PYTHON) tools/materialize.py --check
	$(PYTHON) tools/analyze_epoch1.py --check
	$(PYTHON) tools/verify_case_study.py

clean:
	rm -rf .materialized dsense_v5_*.csv dsense_v5_*.dsb
