# Conformance corpus

`conformance-corpus/expected.json` defines deterministic expected outcomes. Run:

```bash
./scripts/run-conformance-corpus
```

The corpus includes evidence-derived PASS fixtures for L1 through L5, an honest
FAIL, an honest UNKNOWN, and a legacy 0.1 bundle. Invalid fixtures cover copied PASS
without evidence, missing and unindexed gates, stale source/reference/evaluator
bindings, duplicate IDs, conflicting path hashes, performance binding and policy
mismatches, nonfinite samples, timestamps, UNKNOWN promotion, final reconciliation,
cumulative levels, extension shadowing, traversal, symlink escape, and missing
runtime schema resources.

The runner prints sorted JSON and returns nonzero when any observed outcome differs
from the machine-readable expectation. It never executes fixture evidence or calls
an external service.
