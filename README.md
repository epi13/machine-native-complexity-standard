# Machine-Native Complexity Standard

MNCS is an open experimental standard for accepting generated or machine-optimized implementations through bounded evidence. MNCDS is its separate development-process specification. Neither is accredited certification.

> **Human readability is relocated, not eliminated.**

## Experimental multilingual and composed evidence

Wave One established non-normative C11, Rust, and Python language profiles and Provider Protocol fixtures. Wave Two adds Go and mixed-language composition without changing MNCS 0.2 or promoting MNCDS 0.1-draft.

Go was selected for bounded worker pools, cancellation, race tooling, module identity, reproducible builds, and straightforward deployment. A profile describes evidence support; it never makes a language compliant.

The Wave Two composed gateway contains:

- a strict C11 decimal-frame parser behind a stable C ABI;
- a generated, identity-bound cgo binding;
- a Go host controlling limits, timeout, child lifecycle, checkpoint output, and readable rollback;
- a Rust authority subprocess using a versioned bounded line protocol;
- first-class native and process boundary contracts;
- deterministic aggregation where `FAIL > UNKNOWN > PASS`.

A required UNKNOWN may become the workflow disposition `REVIEW_REQUIRED`, but it cannot become system PASS. Component and boundary results retain their original identities and environments.

```bash
make language-profile-schema
make language-provider-corpus
make multilingual-wave-one
make go-profile
make go-provider-corpus
make go-gateway
make composed-gateway
make multilingual-wave-two
```

Provider execution and heavy case-study tooling remain explicit. Ordinary offline validation never launches a compiler, candidate, generator, provider, benchmark, or service.

## Research case studies

- [EdgeStream](case-studies/edgestream/README.md) — C11 telemetry processing.
- [CacheForge](case-studies/cacheforge/README.md) — Python AI/ML cache planning.
- [Multilingual Stream](case-studies/multilingual-stream/README.md) — shared C11/Rust contract.
- [Go Gateway](case-studies/go-gateway/README.md) — bounded concurrency and cancellation.
- [Composed Gateway](case-studies/composed-gateway/README.md) — C11 FFI, generated Go binding, and Rust subprocess authority.
- [Remote Water Control](case-studies/remote-water-control/README.md), [RAVEL](case-studies/ravel/README.md), and [dSense](case-studies/dsense-desk-pet/README.md) — additional bounded research studies.

## Claim boundary

Wave Two is experimental. The checked-in composed record is `REVIEW_REQUIRED`; formal MNCS and MNCDS status remain `UNKNOWN`; promotion is not authorized; and D4 is unclaimed. Protected holdout, independent evaluation, cross-host reproduction, exhaustive deadlock absence, production ABI portability, and an independently witnessed release replacement drill remain outside the evidence.

## Repository map

- `spec/` — MNCS 0.2 and MNCDS 0.1-draft.
- `schemas/` — normative and experimental schemas.
- `experimental/language-evidence/` — profiles, providers, and fixtures.
- `case-studies/` — bounded development studies.
- `docs/` — documentation.
- `rfcs/` — governance proposals, including RFC 0006 and RFC 0007.

Read `CONTRIBUTING.md`, `GOVERNANCE.md`, and the RFC process before proposing normative changes.
