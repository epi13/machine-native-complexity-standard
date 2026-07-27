# Structural-harness feedback

The local bounded source checker completed seven candidate-bound checks and found no
runtime-correlated defect. It was useful as a fast rejection gate for generated markers,
fixed-capacity storage, frame-length validation, validation-before-output ordering,
checkpoint integrity, prohibited benchmark specialization, and processor-path allocation.

Joern was not installed in the captured environment. Joern-specific query outcomes are
therefore UNKNOWN, not PASS. The study supports these next-epoch harness improvements:

1. Preserve each disagreement between runtime differential evaluation and structural
   analysis as a regression fixture.
2. Report unsupported syntax, timeout, and checker failure separately from an invariant
   PASS.
3. Prefer compact repair feedback only when a concrete location and violated invariant
   are available.
4. Bind every query result to candidate, contract, provider, and environment identities.
5. Keep performance measurements separate from structural findings; this study does not
   show that structural feedback caused the measured speedup.

The machine-readable ledger is in `evidence/results/structural.json`.
