# Machine-Native Complexity Standard

MNCS is an open experimental standard for accepting generated or machine-optimized implementations through bounded evidence. MNCDS is its separate development-process specification. Neither is accredited certification.

> **Human readability is relocated, not eliminated.**

## Release-candidate foundation

The repository now contains implementation-ready proposals for MNCS 0.3-rc.1 and
MNCDS 0.1-rc.1. They add contract adequacy, dependency/composition graphs,
freshness and material-change invalidation, partial revalidation, lifecycle records,
an offline MNCDS aggregate, a 74-case golden corpus, independent Python/Rust
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

## Execution assurance for test evidence

The experimental execution-assurance companion record keeps a test result separate from the
integrity, isolation, attestation, and custody of the environment that produced it. It binds the
canonical MNCS or MNCDS subject identity to a test bundle, execution policy, runner, environment,
fresh challenge, explicit assurance properties, and attestation class.

A functional test `PASS` combined with missing or unsupported isolation remains `UNKNOWN` when a
combined PASS is required. Local hashes or signatures cannot establish host-root resistance,
protected custody, or organizational independence.

```bash
mncs-test-evidence validate measurement \
  examples/release-candidate-0.3/measurement-profile.json \
  execution-assurance.json --require-pass --json

mncds-test-evidence validate \
  examples/mncds-0.1-rc/development-record.json \
  execution-assurance.json --require-pass --json
```

The validator remains offline and does not launch a sandbox. See
[execution assurance](docs/execution-assurance.md), the
[implementation next steps](docs/execution-assurance-next-steps.md), and
[draft RFC 0008](rfcs/0008-execution-assurance.md).

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

## Networked evolution model

MNCS and MNCDS define versioned standards, identities, invariants, comparison rules, and
development controls. MNCS Language and other implementations expose semantic and
compiler structures. Forge runs bounded micro-verifiers and candidate checks. RAVEL and
other mechanisms coordinate experiments across agents, machines, implementations, and
trust boundaries. Independent evaluators and custodians challenge the resulting
evidence. Promotion policy and governance alone decide whether a proposal is selected,
standardized, released, rejected, or retained as `UNKNOWN`.

The [networked standard evolution](docs/networked-standard-evolution.md) document
separates implementation refinement from evolution of the standard itself. Evidence may
inform an RFC, but no language, compiler, verifier, Forge workflow, RAVEL mechanism, or
recursive loop can silently rewrite normative meaning or promote its own result.

The experimental [intent-aware security verification](docs/intent-aware-security-verification.md)
design note proposes invariant-driven security micro-verification that preserves useful
non-orthodox implementation intent. Suspicious constructs request bounded evidence
rather than automatic normalization; declared intent never waives a failed safety
property, and missing exploit-chain evidence never converts a confirmed weakness into
`PASS`.

## Research case studies

- [EdgeStream](case-studies/edgestream/README.md) — C11 telemetry processing.
- [CacheForge](case-studies/cacheforge/README.md) — Python AI/ML cache planning.
- [Multilingual Stream](case-studies/multilingual-stream/README.md) — shared C11/Rust contract.
- [Go Gateway](case-studies/go-gateway/README.md) — bounded concurrency and cancellation.
- [Composed Gateway](case-studies/composed-gateway/README.md) — C11 FFI, generated Go bindings, Go orchestration, Rust authority, recovery, measurement, custody, claim readiness, and portable physical-host reproduction.
- [Remote Water Control](case-studies/remote-water-control/README.md), [RAVEL 0.1–0.6](case-studies/ravel/README.md), and [dSense](case-studies/dsense-desk-pet/README.md) — additional bounded studies with explicit non-promotion boundaries.

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
local, physical-machine, Arduino, external-actor, and governance work. The
[Codex implementation next steps](docs/codex-next-steps.md) turn the larger remaining
engineering findings into bounded follow-on tasks with acceptance criteria and explicit
external-actor limits.

## Experimental execution placement

The [execution-placement evidence profile](docs/execution-placement-evidence.md) records
requested policy, observed CPU/accelerator/sequential-offload placement, provider
lifetime versus physical residency, probes, bounded fallback, and resource
observations. It is experimental and non-normative: placement evidence is not
correctness, conformance, independence, security, or promotion evidence.

The [experimental typed execution receipt](docs/execution-receipts.md) is the
runner-produced observation envelope for lifecycle, output, resource, enforcement,
and optional placement facts. It records what happened and does not itself create
execution assurance, conformance, sandbox, custody, independence, or promotion.

The [experimental immutable execution bundle](docs/execution-bundles.md) freezes
bounded test material beneath that receipt with separate canonical manifest and
deterministic archive identities. It establishes package integrity only; it is not
a sandbox, execution-assurance verdict, conformance result, custody record, or
promotion authority.

The [experimental execution challenge and replay profile](docs/execution-challenges.md)
adds verifier-issued, scope-bound nonces and explicit single-use consumption. Its local
replay store detects reuse within its declared boundary and persists a monotonic time
watermark; it does not establish correctness, isolation, custody, independence,
conformance, or promotion.

```bash
mncs schema execution-receipt-0.1-experimental --json
mncs validate-execution-receipt receipt.json --json
mncs challenge validate challenge.json --json
```

## Repository map

- `spec/` — frozen MNCS 0.2/MNCDS draft and the 0.3/0.1 release candidates.
- `schemas/` — normative and experimental schemas.
- `conformance/release-candidate/` — shared MNCS/MNCDS golden vectors.
- `independent/rc-consumer/` — independent Rust release-candidate consumer.
- `studies/recursive-analyzer/` — controlled two-epoch recursive study.
- `experimental/language-evidence/` — profiles, providers, and fixtures.
- `experimental/execution-placement/` — experimental resource-placement evidence fixtures.
- `experimental/execution-receipt/` — experimental immutable runner-receipt fixtures.
- `experimental/execution-bundle/` — experimental immutable execution-bundle source and fixtures.
- `experimental/execution-challenge/` — experimental challenge/replay request and adversarial fixtures.
- `case-studies/` — bounded development studies and evidence epochs.
- `docs/` — documentation.
- `rfcs/` — governance proposals, including RFC 0006, RFC 0007, and RFC 0008.

Read `CONTRIBUTING.md`, `GOVERNANCE.md`, and the RFC process before proposing normative changes.

## Dependency compatibility boundary

The maintenance baseline uses Ruff 0.16.0 and the current compatible major versions
of the GitHub Actions used by the workflows. The `cryptography` bound remains
`>=43,<47`: cryptography 49 removes x86_64 macOS and 32-bit Windows support, while
the repository's workflow and portability evidence still include macOS and Windows.
That bound should be revisited only with an explicit supported-architecture decision
and an installed-package matrix covering those platforms.
