# Experimental composed systems

A language profile describes bounded evidence capabilities. It does not certify a language, compiler, runtime, analyzer, component, or system. Composition therefore starts from independently scoped component and boundary results rather than treating language choice as a proxy for correctness.

## Composition rule

Every required result keeps its original subject, provider, contract, environment, and evidence identity. Aggregation applies:

1. `FAIL` dominates every other outcome.
2. Otherwise `UNKNOWN` dominates `PASS`.
3. Missing required evidence is `UNKNOWN`.
4. A policy may translate required uncertainty to `REVIEW_REQUIRED` for workflow continuation.
5. `REVIEW_REQUIRED` never becomes formal MNCS or MNCDS PASS.

A component PASS cannot erase a boundary FAIL. A boundary PASS cannot erase a component FAIL. Unsupported analysis and unavailable tools cannot be converted to PASS through aggregation.

## Wave Three evidence epoch

The Wave Three composed gateway creates new identities rather than editing Wave Two evidence. It records:

- system contract and preregistration identities;
- C header, generated cgo binding, generator, Go host, Rust authority, and protocol identities;
- strict build, unit, vet, race, fuzz, regeneration, recovery, replacement, mutation, and measurement outcomes;
- local development, public hosted reproduction, and protected holdout partitions;
- a second aggregation implementation that is explicitly not an independent evaluator;
- formal MNCS and MNCDS statuses separately from the development disposition.

## Checkpoint and restore

A checkpoint binds the system contract, C header, binding specification, binding generator, authority, canonical input digest, processed count, accumulated state, and state digest. Writes use a temporary file followed by an atomic rename. Restore rejects stale input, partial state, unknown fields, incompatible binding identity, authority mismatch, and out-of-range progress.

The only declared replacement path is from `rust-authority-v2` to `go-readable-authority-v2`, and it requires an explicit authorization flag. The continued execution digest must match uninterrupted execution.

## Generated bindings

The cgo binding is regenerated from the C header and a binding specification. The record binds:

- header hash;
- binding-specification hash;
- generator identity and source hash;
- normalized gofmt output hash;
- ABI version;
- exact regeneration command.

Drift fails before compatibility and recovery tests. A generator may not silently alter integer width, ownership, error mapping, or ABI version.

## Measurements

Wave Three uses two warmups and nine retained repetitions. Readable and composed order alternates; checkpoint mode follows each pair. The report retains wall time, child user and system CPU, maximum RSS observation, throughput, process-boundary overhead, checkpoint overhead, recovery time, fallback events, proposal rejections, and bounded Go component benchmarks.

RSS units are platform dependent. Process overhead includes serialization and child lifecycle and is not presented as a global language comparison. No observation is removed as an outlier.

## Holdout and independent evaluation

The public repository contains a commitment and input interface, not a protected corpus. In the absence of external custody records, protected holdout remains `UNKNOWN`. Public development or CI traces cannot be relabeled as protected.

The second evaluator implementation checks schema validity, outcome precedence, holdout labeling, formal claim boundaries, and the regeneration/replacement subclaim. It is structurally separate but not organizationally independent, so independent evaluation remains `UNKNOWN`.

## D4 boundary

A successful binding regeneration and readable replacement execution supports a narrow regeneration/replacement drill subclaim. Full MNCDS-D4 additionally requires controlled release approval, independently witnessed replacement, production monitoring, rollback thresholds, retirement triggers, and retained evidence custody. Wave Three does not claim those controls.

## Reproduction

```bash
make composed-wave-three
make multilingual-wave-three
```

The full job requires Go 1.23.x, Rust 1.97.1, Python 3.11 or later, cgo, and a strict C11 compiler. CI executes the epoch on Ubuntu and macOS and uploads separate immutable workflow artifacts. Hosted artifacts require review before a checked-in claim can be changed.
