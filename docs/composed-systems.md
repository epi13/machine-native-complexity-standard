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

Wave Three created new identities rather than editing Wave Two evidence. It records system and preregistration identities; C header, binding, generator, Go host, Rust authority, and protocol identities; build, recovery, mutation, and measurement outcomes; development, hosted reproduction, and protected partitions; and separate MNCS and MNCDS statuses.

Checkpoints bind the system contract, C header, binding specification, binding generator, authority, canonical input digest, processed count, accumulated state, and state digest. Restore rejects stale input, partial state, unknown fields, incompatible binding identity, authority mismatch, and out-of-range progress. The declared replacement path from `rust-authority-v2` to `go-readable-authority-v2` requires explicit authorization and digest equivalence.

## Wave Four evidence custody

Wave Four adds records that can be supplied by actors outside the development process. A protected evidence record binds:

- preregistration and candidate-freeze identities;
- protected corpus identity;
- custodian and evaluator identities and organizations;
- raw and normalized result identities;
- attestation identity;
- preregistration, freeze, disclosure, and evaluation timestamps;
- explicit confirmation that the corpus is not embedded publicly and was unavailable to development participants before disclosure.

The reference verifier rejects self-custody, self-evaluation, invalid timestamp order, missing identities, and attempts to relabel public development evidence. Software can check record consistency, but organizational independence remains an externally attested fact.

## Cross-host agreement

Cross-host reconciliation requires at least two distinct environments. The reconciler compares:

- system contract and evidence epoch;
- component, binding, generator, and tool identities;
- all required build, recovery, replacement, and mutation gates;
- semantic output digests.

An identity or semantic mismatch is `FAIL`. An unavailable required gate is `UNKNOWN`. Agreement becomes `PASS` only when all required host records pass under the same frozen identities. Synthetic fixtures test the reconciler but are not reproduction evidence.

## Service boundary

Wave Four adds a bounded Go HTTP service on `127.0.0.1` with an ephemeral port. The service uses exact `V1` JSON messages, a 1,024-byte body limit, a bounded integer domain, strict unknown-field rejection, caller cancellation, bounded shutdown, and identity-bound restart policy. Tests cover valid execution, malformed JSON, unknown fields, wrong method, version mismatch, oversized body, cancellation, shutdown, and restart.

Loopback tests establish only the declared local transport contract. Production networking, reverse proxies, orchestration, kernel variance, and service-manager behavior outside the simulated restart remain `UNKNOWN`.

## Separate claim readiness

Wave Four never combines implementation and lifecycle claims into one score.

MNCS readiness requires the development epoch, cross-host agreement, protected holdout, independent evaluation, and service boundary to pass. MNCDS-D4 readiness additionally requires deterministic regeneration, a witnessed replacement drill, release controls, monitoring, retirement controls, and an independent witness. Release authorization is a separate required result.

A failure in either claim family produces a failed readiness disposition. Missing external evidence leaves the corresponding formal result `UNKNOWN` and the workflow disposition `REVIEW_REQUIRED`. Promotion is permitted only when both formal results and release authorization are PASS.

## Monitoring and retirement

The Wave Four release policy defines immediate rollback for identity mismatch or fallback failure, bounded thresholds for protocol rejection, timeout, and memory growth, and a readable rollback target. Retirement triggers include incompatible boundaries, unsupported toolchains, unresolved identity mismatches, repeated rollback thresholds, expired evidence policy, or acceptance of a replacement under a new identity.

These policies are design evidence. They remain `UNKNOWN` as operational D4 evidence until exercised in a controlled release environment and independently witnessed.

## Reproduction

```bash
make composed-wave-three
make multilingual-wave-three
make composed-wave-four
make multilingual-wave-four
```

Wave Four requires Go 1.23.x and Python 3.11 or later for its local checks. Cross-host reconciliation consumes the separate Wave Three Ubuntu and macOS artifacts. Protected evaluation requires a custody record and corpus supplied after candidate freeze by external actors.
