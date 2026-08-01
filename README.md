# Machine-Native Complexity Standard

MNCS is an open experimental standard for accepting generated or machine-optimized implementations through bounded evidence. MNCDS is its separate development-process specification. Neither is accredited certification.

> **Human readability is relocated, not eliminated.**

## Release-candidate foundation

The repository now contains implementation-ready proposals for MNCS 0.3-rc.1 and
MNCDS 0.1-rc.1. They add contract adequacy, dependency/composition graphs,
freshness and material-change invalidation, partial revalidation, lifecycle records,
an offline MNCDS aggregate, a 72-case golden corpus, independent Python/Rust
agreement, and a reproducible two-epoch improvement study.

Both RFC 0004 and RFC 0005 remain Draft. Independent operation, organizational
independence, externally protected custody, security/privacy acceptance, governance
approval, and final release authorization remain OPEN or UNKNOWN.

```bash
make release-candidate-check
mncs validate-record assurance examples/release-candidate-0.3/assurance-case.json
mncds validate examples/mncds-0.1-rc/development-record.json
mncs corpus release-candidate --json
```

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

The separate [MNCS Forge MCP integration](docs/mncs-forge.md) is an optional,
experimental, non-normative Codex control plane. It does not replace Provider Protocol
or offline MNCS/MNCDS validation and cannot create independent or protected evidence.

## Research case studies

- [EdgeStream](case-studies/edgestream/README.md) — C11 telemetry processing.
- [CacheForge](case-studies/cacheforge/README.md) — Python AI/ML cache planning.
- [Multilingual Stream](case-studies/multilingual-stream/README.md) — shared C11/Rust contract.
- [Go Gateway](case-studies/go-gateway/README.md) — bounded concurrency and cancellation.
- [Composed Gateway](case-studies/composed-gateway/README.md) — C11 FFI, generated Go bindings, Go orchestration, Rust authority, recovery, measurement, custody, claim readiness, and portable physical-host reproduction.
- [Remote Water Control](case-studies/remote-water-control/README.md), [RAVEL 0.1–0.5](case-studies/ravel/README.md), and [dSense](case-studies/dsense-desk-pet/README.md) — additional bounded studies with explicit non-promotion boundaries.

## Current claim boundary

Two of the five Wave Five physical-host records, Fedora-A and PiOS-ARM, have been
collected and validated. The physical-machine cohort remains `UNKNOWN` until all five
host records are collected. A passing cohort can set operator-controlled public
reproduction to `PASS` because it covers distinct machines, Windows and Linux,
multiple distributions, and x86-64 plus ARM. It still cannot establish protected
holdout, organizationally independent evaluation, or an independent witness because
the same project operator controls the machines.

Formal MNCS and MNCDS statuses remain `UNKNOWN`, promotion is prohibited, and full MNCDS-D4 is unclaimed. The repository can validate externally supplied evidence; it cannot self-create independence or protected custody.

The [post-Wave-Five roadmap](docs/post-wave-five-roadmap.md) separates the remaining
local, physical-machine, Arduino, external-actor, and governance work.

## Repository map

- `spec/` — frozen MNCS 0.2/MNCDS draft and the 0.3/0.1 release candidates.
- `schemas/` — normative and experimental schemas.
- `conformance/release-candidate/` — shared MNCS/MNCDS golden vectors.
- `independent/rc-consumer/` — independent Rust release-candidate consumer.
- `studies/recursive-analyzer/` — controlled two-epoch recursive study.
- `experimental/language-evidence/` — profiles, providers, and fixtures.
- `case-studies/` — bounded development studies and evidence epochs.
- `docs/` — documentation.
- `rfcs/` — governance proposals, including RFC 0006 and RFC 0007.

Read `CONTRIBUTING.md`, `GOVERNANCE.md`, and the RFC process before proposing normative changes.
