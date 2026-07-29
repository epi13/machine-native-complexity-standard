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

Wave Four adds records that can be supplied by actors outside the development process. A protected evidence record binds preregistration and candidate-freeze identities, protected corpus identity, actor identities, raw and normalized result identities, attestation identity, disclosure chronology, and confirmation that the corpus was unavailable to development participants before disclosure.

The reference verifier rejects self-custody, self-evaluation, invalid timestamp order, missing identities, and attempts to relabel public development evidence. Software can check record consistency, but organizational independence remains an externally attested fact.

## Cross-host agreement

Wave Four cross-host reconciliation compares system contract, evidence epoch, component, binding, generator, tool, recovery, mutation, and semantic-output identities. An identity or semantic mismatch is `FAIL`. An unavailable required gate is `UNKNOWN`. Synthetic fixtures test the reconciler but are not reproduction evidence.

## Service boundary

Wave Four adds a bounded Go HTTP service on `127.0.0.1` with an ephemeral port. It uses exact `V1` JSON messages, a 1,024-byte body limit, a bounded integer domain, strict unknown-field rejection, caller cancellation, bounded shutdown, and identity-bound restart policy.

Loopback tests establish only the declared local transport contract. Production networking, reverse proxies, orchestration, kernel variance, and service-manager behavior outside the simulated restart remain `UNKNOWN`.

## Wave Five portable evaluator

Wave Five freezes a small evaluator bundle that can be copied unchanged to physical machines. The bundle uses Python 3.9 or later and the standard library only. Its deterministic ZIP uses stored entries and fixed metadata so the archive, manifest, evaluator, workload, and candidate-freeze identities can be checked before execution.

Each host record retains:

- the frozen bundle and manifest identities;
- the transport archive identity when supplied;
- machine label and hashed machine fingerprint;
- operator identity and evidence class;
- OS family, distribution, architecture, Python runtime, and CPU count;
- optional Go, Rust, and C compiler observations;
- bundle integrity, deterministic vectors, checkpoint resume, corruption rejection, and offline-capability gates;
- semantic and raw-artifact identities;
- explicit protected-holdout and independent-evaluation statuses.

The portable contract is narrower than the full C11/Go/Rust epoch. It checks deterministic behavioral and recovery semantics plus bundle portability; it does not replace compiler, race, mutation, FFI, or subprocess evidence.

## Operator-controlled physical cohort

The preregistered Wave Five physical cohort contains:

- `windows-a` and `windows-b`;
- `fedora-a` and `fedora-b`;
- `pios-arm`.

A cohort PASS requires all five records, one frozen bundle and candidate identity, one semantic output digest, all required gates PASS, at least two OS families, three distribution classes, and two normalized architectures.

When one project operator runs all five machines, the evidence class is `OPERATOR_CONTROLLED_CROSS_HOST`. This can set public reproduction to PASS and is materially stronger than a single development machine. It cannot set independent evaluation or protected holdout to PASS because machine diversity is not actor or custody independence.

## Separate claim readiness

MNCS readiness requires the development epoch, public reproduction, protected holdout, independent evaluation, and all required boundaries to pass. MNCDS-D4 readiness additionally requires deterministic regeneration, a witnessed replacement drill, release controls, monitoring, retirement controls, and an independent witness. Release authorization remains separate.

A failure in either claim family produces a failed readiness disposition. Missing external evidence leaves the corresponding formal result `UNKNOWN` and the workflow disposition `REVIEW_REQUIRED`. Promotion is permitted only when both formal results and release authorization are PASS.

## Monitoring and retirement

The Wave Four release policy defines immediate rollback for identity mismatch or fallback failure, bounded thresholds for protocol rejection, timeout, and memory growth, and a readable rollback target. Retirement triggers include incompatible boundaries, unsupported toolchains, unresolved identity mismatches, repeated rollback thresholds, expired evidence policy, or acceptance of a replacement under a new identity.

These policies remain `UNKNOWN` as operational D4 evidence until exercised in a controlled release environment and independently witnessed.

## Reproduction

```bash
make composed-wave-three
make multilingual-wave-three
make composed-wave-four
make multilingual-wave-four
make composed-wave-five
make multilingual-wave-five
```

Wave Five builds a portable artifact and runs reference smoke tests on hosted Windows, Ubuntu, and macOS runners. The physical Windows, Fedora, and Pi OS records must be collected separately using the exact checked-in archive identity. Protected evaluation still requires a corpus and custody record supplied after candidate freeze by external actors.
