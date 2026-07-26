# Performance evidence

Performance measurement MUST be gated by correctness and MUST distinguish a valid
measurement from a victory. Repetitions, representative corpora, randomized or
alternating order, semantic checksums, noise policy, worst-corpus regression,
platform, compiler, build, binary size, and memory are REQUIRED at L4.

A useful threshold MUST be declared before candidate generation. Valid objectives
include throughput, latency, memory, binary size, energy, reliability, hardware
utilization, and verified state-space coverage. Performance is not the only valid
objective. Post-hoc substitution creates a new evaluation series and MUST NOT reuse
the old victory claim.
Performance evidence is required only for L4 and L5. A schema 0.1.1 record binds
contract, candidate and reference hashes; evaluator, harness, environment, build,
and corpus identities; metric, unit, direction, threshold, noise policy, sample
order, samples and counts; semantic identity; summaries; regression data; and
timestamps.

Validators MUST reject objective/unit/direction mismatch, stale hashes, missing
identity records, nonfinite or negative samples, insufficient counts, failed
required checksums, inconsistent sample order or summaries, and malformed time
ordering. Measurement validity, benefit threshold, and worst-regression status are
derived. A claimed performance victory cannot survive invalid measurement.
