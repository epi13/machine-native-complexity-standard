# Machine-Native Complexity Standard

MNCS is an open experimental standard for accepting generated or machine-optimized implementations through bounded evidence. MNCDS is its separate development-process specification. Neither is accredited certification.

> **Human readability is relocated, not eliminated.**

## Experimental multilingual and composed evidence

Wave One established non-normative C11, Rust, and Python language profiles. Wave Two added Go, native FFI and process boundaries, generated bindings, and composed-result propagation. Wave Three added identity-bound recovery, mutation, measurement, replacement, and hosted evidence jobs. Wave Four added evidence custody, cross-host reconciliation, claim readiness, and a bounded service boundary.

Wave Five adds a portable, sealed evaluator for physical machines outside GitHub Actions:

- deterministic ZIP and manifest identities;
- Python 3.9+ standard-library execution on Windows, Fedora, and Raspberry Pi OS;
- host records for bundle integrity, semantic vectors, checkpoint recovery, corruption rejection, environment, and optional toolchains;
- a preregistered five-machine plan covering two Windows computers, two Fedora computers, and one Pi OS ARM computer;
- an explicit evidence class for operator-controlled cross-host reproduction;
- separate public-reproduction, protected-holdout, and independent-evaluation statuses.

Every component, boundary, host, and cohort retains its own identity and environment. `FAIL` dominates `UNKNOWN`, and `UNKNOWN` dominates `PASS`. `REVIEW_REQUIRED` is a workflow disposition, not a formal MNCS result.

```bash
make language-profile-schema
make language-provider-corpus
make multilingual-wave-one
make multilingual-wave-two
make multilingual-wave-three
make multilingual-wave-four
make multilingual-wave-five
```

Provider execution, compilers, generators, benchmarks, services, custody verification, and portable host execution remain explicit. Ordinary offline validation never launches them.

## Research case studies

- [EdgeStream](case-studies/edgestream/README.md) — C11 telemetry processing.
- [CacheForge](case-studies/cacheforge/README.md) — Python AI/ML cache planning.
- [Multilingual Stream](case-studies/multilingual-stream/README.md) — shared C11/Rust contract.
- [Go Gateway](case-studies/go-gateway/README.md) — bounded concurrency and cancellation.
- [Composed Gateway](case-studies/composed-gateway/README.md) — C11 FFI, generated Go bindings, Go orchestration, Rust authority, recovery, measurement, custody, claim readiness, and portable physical-host reproduction.
- [Remote Water Control](case-studies/remote-water-control/README.md), [RAVEL](case-studies/ravel/README.md), and [dSense](case-studies/dsense-desk-pet/README.md) — additional bounded studies.

## Current claim boundary

The checked-in Wave Five physical-machine cohort remains `UNKNOWN` until the five host records are collected. A passing cohort can set operator-controlled public reproduction to `PASS` because it covers distinct machines, Windows and Linux, multiple distributions, and x86-64 plus ARM. It still cannot establish protected holdout, organizationally independent evaluation, or an independent witness because the same project operator controls the machines.

Formal MNCS and MNCDS statuses remain `UNKNOWN`, promotion is prohibited, and full MNCDS-D4 is unclaimed. The repository can validate externally supplied evidence; it cannot self-create independence or protected custody.

## Repository map

- `spec/` — MNCS 0.2 and MNCDS 0.1-draft.
- `schemas/` — normative and experimental schemas.
- `experimental/language-evidence/` — profiles, providers, and fixtures.
- `case-studies/` — bounded development studies and evidence epochs.
- `docs/` — documentation.
- `rfcs/` — governance proposals, including RFC 0006 and RFC 0007.

Read `CONTRIBUTING.md`, `GOVERNANCE.md`, and the RFC process before proposing normative changes.
