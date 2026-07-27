# EdgeStream MNCS case study

EdgeStream is a fault-tolerant, bounded C11 telemetry processor used as the second major
MNCS research example. It compares a readable reference with a deterministic generated
candidate across stateful parsing, malformed input, alarms, resource pressure,
checkpoint recovery, compiler/sanitizer checks, structural rejection checks, and paired
performance measurements.

The checked-in development evidence derives `MNCS-L4 PASS` for the declared contract and
captured environment. The companion process record targets `MNCDS-D2`; it does not claim
independent protected holdout or lifecycle release assurance. These are experimental
results, not accredited certification or a production-safety claim.

## Run

```bash
python tools/run_study.py all
python tools/package_evidence.py
mncs validate-bundle . --require-pass
mncds validate mncds/development-record.json --require-pass
```

The full study requires Python 3.11+, a C11 compiler, and preferably both GCC and Clang.
Generated binaries and workload byte streams are excluded from version control. Compact
workload identities and the captured result records are committed.

## Results from the captured run

- Reference and candidate outputs matched for all declared workloads and fragment sizes.
- GCC and Clang strict-warning builds passed.
- AddressSanitizer and UndefinedBehaviorSanitizer runs passed.
- Checkpoint restoration and four injected failure points passed.
- The generated candidate exceeded the 1.15 throughput threshold in the captured run.
- Joern was unavailable; the local bounded structural provider passed and Joern-specific
  evidence remains explicitly UNKNOWN.

See `evidence/results/study-summary.json` and `evidence/results/benchmark.json` for the
machine-readable observations.
