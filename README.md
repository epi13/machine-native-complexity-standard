# Machine-Native Complexity Standard

MNCS is an open experimental standard for accepting generated or machine-optimized implementations through bounded evidence. MNCDS is its separate development-process specification. Neither is accredited certification.

> **Human readability is relocated, not eliminated.**

## Experimental multilingual and composed evidence

Wave One established non-normative C11, Rust, and Python language profiles and Provider Protocol fixtures. Wave Two added Go, native FFI and process boundary contracts, generated bindings, and composed-result propagation without changing MNCS 0.2 or promoting MNCDS 0.1-draft.

Wave Three adds a measured composition epoch while preserving every Wave Two identity and historical claim. The new epoch includes:

- a versioned Go host with atomic, identity-bound checkpoints;
- a pinned Rust 1.97.1 authority using a new `V2` process protocol;
- deterministic generated-binding regeneration and drift detection;
- restart, restore, stale-state rejection, and readable replacement drills;
- eighteen retained fault, operational-error, and UNKNOWN fixtures;
- repeated component and system resource measurements with no outlier removal;
- a second aggregation implementation;
- Ubuntu and macOS hosted reproduction artifact jobs;
- an explicit protected-holdout commitment that remains `UNKNOWN` without external custody.

Every component and boundary retains its own evidence and environment. `FAIL` dominates `UNKNOWN`, and `UNKNOWN` dominates `PASS`. `REVIEW_REQUIRED` is a workflow disposition, not a formal MNCS result.

```bash
make language-profile-schema
make language-provider-corpus
make multilingual-wave-one
make go-profile
make go-provider-corpus
make multilingual-wave-two
make multilingual-wave-three
```

Provider execution, compilers, generators, benchmarks, and services remain explicit. Ordinary offline validation never launches them.

## Research case studies

- [EdgeStream](case-studies/edgestream/README.md) — C11 telemetry processing.
- [CacheForge](case-studies/cacheforge/README.md) — Python AI/ML cache planning.
- [Multilingual Stream](case-studies/multilingual-stream/README.md) — shared C11/Rust contract.
- [Go Gateway](case-studies/go-gateway/README.md) — bounded concurrency and cancellation.
- [Composed Gateway](case-studies/composed-gateway/README.md) — C11 FFI, generated Go bindings, Go orchestration, Rust authority, recovery, and replacement evidence.
- [Remote Water Control](case-studies/remote-water-control/README.md), [RAVEL](case-studies/ravel/README.md), and [dSense](case-studies/dsense-desk-pet/README.md) — additional bounded studies.

## Current claim boundary

The checked-in Wave Three local development epoch is `REVIEW_REQUIRED`. C11, generated-binding, Go unit, Go vet, Go race, Go fuzz, readable checkpoint, identity-rejection, and local measurement gates pass in the recorded environment. Rust-dependent process recovery, replacement, mutation, and cross-host evidence remain pending the hosted artifacts. Formal MNCS and MNCDS status remain `UNKNOWN`, promotion is prohibited, and full MNCDS-D4 is unclaimed.

A successful hosted replacement drill can support only the narrow regeneration/replacement subclaim. It cannot establish D4 without release controls, production monitoring, retirement policy, protected evidence custody, and independent witnessing.

## Repository map

- `spec/` — MNCS 0.2 and MNCDS 0.1-draft.
- `schemas/` — normative and experimental schemas.
- `experimental/language-evidence/` — profiles, providers, and fixtures.
- `case-studies/` — bounded development studies and evidence epochs.
- `docs/` — documentation.
- `rfcs/` — governance proposals, including RFC 0006 and RFC 0007.

Read `CONTRIBUTING.md`, `GOVERNANCE.md`, and the RFC process before proposing normative changes.
