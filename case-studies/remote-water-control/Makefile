.PHONY: generate check-generated test smoke study protected clean

PYTHONPATH := src:machine

generate:
	PYTHONPATH=$(PYTHONPATH) python tools/generate_planner.py

check-generated:
	PYTHONPATH=$(PYTHONPATH) python tools/generate_planner.py --check

test: check-generated
	PYTHONPATH=$(PYTHONPATH) pytest -q

smoke: check-generated
	PYTHONPATH=$(PYTHONPATH) python tools/run_study.py smoke

study: test
	PYTHONPATH=$(PYTHONPATH) python tools/run_study.py all

protected: test
	test -n "$(PROTECTED_SEED)"
	PYTHONPATH=$(PYTHONPATH) python tools/run_protected_evaluation.py \
		--seed "$(PROTECTED_SEED)" \
		--output evidence/protected/local.json

clean:
	rm -f evidence/results/scenario-results.json.gz evidence/results/study-summary.json.gz
	rm -rf evidence/protected
