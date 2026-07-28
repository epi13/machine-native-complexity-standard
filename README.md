# Machine-Native Complexity Standard

MNCS is an open experimental standard for accepting generated or machine-optimized implementations through bounded evidence. MNCDS is its separate development-process specification. Neither is accredited certification.

> **Human readability is relocated, not eliminated.**

## Experimental multilingual and composed evidence

Wave One established non-normative C11, Rust, and Python language profiles and Provider Protocol fixtures. Wave Two added Go, native FFI and process boundary contracts, generated bindings, and composed-result propagation. Wave Three added identity-bound recovery, mutation, measurement, replacement, and Ubuntu/macOS evidence jobs.

Wave Four adds the claim-readiness layer without changing MNCS 0.2 or promoting MNCDS 0.1-draft:

- protected-holdout custody and disclosure records;
- developer, custodian, evaluator, witness, and release-authority separation;
- cross-host artifact reconciliation by contract, epoch, component, tool, and semantic identities;
- separate MNCS implementation and MNCDS lifecycle readiness aggregation;
- a bounded Go loopback HTTP service boundary with cancellation, malformed-input, size, shutdown, and restart tests;
- release monitoring, rollback, and retirement policies;
- explicit `UNKNOWN` when external custody, independence, witnessing, or production evidence is absent.

Every component and boundary retains its own evidence and environment. `FAIL` dominates `UNKNOWN`, and `UNKNOWN` dominates `PASS`. `REVIEW_REQUIRED` is a workflow disposition, not a formal MNCS result.

```bash
make language-profile-schema
make language-provider-corpus
make multilingual-wave-one
make multilingual-wave-two
make multilingual-wave-three
make multilingual-wave-four
```

Provider execution, compilers, generators, benchmarks, services, and custody verification remain explicit. Ordinary offline validation never launches them.

## Research case studies

- [EdgeStream](case-studies/edgestream/README.md) — C11 telemetry processing.
- [CacheForge](case-studies/cacheforge/README.md) — Python AI/ML cache planning.
- [Multilingual Stream](case-studies/multilingual-stream/README.md) — shared C11/Rust contract.
- [Go Gateway](case-studies/go-gateway/README.md) — bounded concurrency and cancellation.
- [Composed Gateway](case-studies/composed-gateway/README.md) — C11 FFI, generated Go bindings, Go orchestration, Rust authority, recovery, measurement, external evidence contracts, and claim readiness.
- [Remote Water Control](case-studies/remote-water-control/README.md), [RAVEL](case-studies/ravel/README.md), and [dSense](case-studies/dsense-desk-pet/README.md) — additional bounded studies.

## Current claim boundary

The checked-in Wave Four local readiness record is `REVIEW_REQUIRED`. The Wave Three development epoch, deterministic regeneration, and Wave Four loopback service-boundary tests are recorded as PASS. Cross-host agreement, protected holdout, organizationally independent evaluation, witnessed replacement, operational monitoring, retirement exercise, and release authorization remain `UNKNOWN`.

Formal MNCS and MNCDS statuses remain `UNKNOWN`, promotion is prohibited, and full MNCDS-D4 is unclaimed. The public repository can validate externally supplied evidence records; it cannot self-create organizational independence or protected custody.

## Repository map

- `spec/` — MNCS 0.2 and MNCDS 0.1-draft.
- `schemas/` — normative and experimental schemas.
- `experimental/language-evidence/` — profiles, providers, and fixtures.
- `case-studies/` — bounded development studies and evidence epochs.
- `docs/` — documentation.
- `rfcs/` — governance proposals, including RFC 0006 and RFC 0007.

Read `CONTRIBUTING.md`, `GOVERNANCE.md`, and the RFC process before proposing normative changes.
