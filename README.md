# Machine-Native Complexity Standard

[![CI](https://github.com/epi13/machine-native-complexity-standard/actions/workflows/ci.yml/badge.svg)](https://github.com/epi13/machine-native-complexity-standard/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Standard](https://img.shields.io/badge/MNCS-0.2-experimental-orange.svg)](spec/MNCS-v0.2.md)
[![Development specification](https://img.shields.io/badge/MNCDS-0.1--draft-purple.svg)](spec/MNCDS-v0.1-draft.md)

MNCS is an open, experimental, tool-neutral standard for accepting generated or
machine-optimized implementations that may exceed ordinary human-maintainability limits.
MNCDS is its companion process specification for controlling how those implementations are
generated, evaluated, selected, released, regenerated, replaced, and retired.

> **Human readability is relocated, not eliminated.**

Readable control remains in contracts, limits, reference behavior, evidence, provenance,
development records, regeneration, rollback, and release policy. Machine-owned internal
complexity is acceptable only when it buys a predeclared measurable benefit inside a bounded,
auditable envelope. Complexity, novelty, or source size alone is never the useful benefit.

MNCS and MNCDS are not accredited ISO, ANSI, IEEE, IETF, or similar standards. MNCS 0.2 and
MNCDS 0.1-draft are experimental and must not be represented as blanket certification.

## Two separate claims

| Claim family | What it evaluates |
|---|---|
| `MNCS-L1` through `MNCS-L5` | Candidate implementation and evidence conformance |
| `MNCDS-D1` through `MNCDS-D4` | Development-process control and lifecycle assurance |

A project may state both only when each result is independently supported. `FAIL` dominates
`UNKNOWN`, and `UNKNOWN` dominates `PASS`; unavailable or unsupported evidence never silently
passes.

## Experimental multilingual evidence layer

[RFC 0006](rfcs/0006-experimental-language-evidence-profiles.md) adds a non-normative,
versioned language-evidence layer for C11, Rust, and Python. A language profile describes how
evidence is collected. It does **not** make a programming language, compiler, interpreter,
runtime, or analyzer MNCS compliant.

Use the terms **profile-valid**, **provider-conformant**, and **evidence-supported** rather than
“MNCS certified.” Provider execution is explicit; ordinary offline MNCS and MNCDS validation
never launches a language provider.

Wave One:

- keeps C11 as the controlled anchor;
- pins Rust 1.97.1 with edition 2024 and a Cargo lockfile;
- binds CacheForge to a CPython 3.11 profile through a new amendment without rewriting history;
- supplies bounded C11, Rust, and Python Provider Protocol 0.1 implementations;
- tests PASS, FAIL, UNKNOWN, crash, timeout, deterministic output, and identity binding;
- runs one shared C11/Rust stream contract without inventing a universal complexity score.

```bash
make language-profile-schema
make language-provider-corpus
make multilingual-stream
make cacheforge-language-profile
make multilingual-wave-one
```

## Foundation and evidence analyzer

[RFC 0005](rfcs/0005-machine-native-foundation-and-evidence-analyzer.md) proposes the broader
conceptual foundation, contract adequacy, applicability and criticality, composition, assurance
cases, and a focused compiler-backed Machine-Native Evidence Analyzer. It remains Draft and does
not change MNCS 0.2 or promote MNCDS.

The analyzer architecture emits bounded PASS, FAIL, or UNKNOWN results. The first prototype uses
Clang AST JSON for a deliberately small C11 invariant set. Joern and other providers remain
optional and replaceable; no product is a normative dependency.

## Install and validate

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
mncs version
mncds version
make check
```

Common MNCS commands:

```text
mncs init PATH
mncs validate MANIFEST
mncs validate-bundle DIRECTORY
mncs certify MANIFEST
mncs certify-bundle DIRECTORY
mncs summarize MANIFEST
mncs compare MANIFEST_A MANIFEST_B
mncs hash PATH
mncs canonicalize FILE
mncs pack BUNDLE --output FILE.mncs
mncs verify-package FILE.mncs
mncs provider inspect COMMAND
mncs provider run DESCRIPTOR REQUEST
mncs provider verify-result RESULT
mncs schema NAME
```

MNCDS process records are validated independently:

```text
mncds validate DEVELOPMENT_RECORD
mncds validate DEVELOPMENT_RECORD --require-pass --json
```

Validation is offline and never executes a generator, candidate, evaluator, analyzer, benchmark,
or evidence binary. Exit 1 means invalid evidence or record semantics, exit 2 means operational
error, and exit 3 means structurally valid but non-PASS under a requested PASS policy.

## Research case studies

- [EdgeStream](case-studies/edgestream/README.md): stateful C11 telemetry processing with strict
  compiler, sanitizer, mutation, recovery, structural, and performance evidence.
- [Remote Water Control](case-studies/remote-water-control/README.md): development-only supervisory
  digital twin with readable safety authority and an explicit formal UNKNOWN boundary.
- [CacheForge](case-studies/cacheforge/README.md): LLM KV-cache planning with generated eviction
  policy, readable authority, deterministic epochs, and a new Python-profile amendment.
- [Multilingual Stream](case-studies/multilingual-stream/README.md): one readable contract across
  C11 and Rust reference/candidate pairs with typed comparability categories.
- [RAVEL](case-studies/ravel/README.md): recursive adaptive vector execution and bounded training.
- [dSense Desk Pet](case-studies/dsense-desk-pet/README.md): constrained Arduino evidence study.

A favorable development result is never automatically a formal MNCS or MNCDS claim. Each study
states its own exact promotion boundary.

## Cumulative levels

### MNCS implementation levels

| Level | Adds |
|---|---|
| MNCS-L1 | Behavioral conformance, readable contract/reference, edge cases, strict tools |
| MNCS-L2 | Runtime and memory safety, malformed inputs, fuzz/property tests, resource limits |
| MNCS-L3 | Tool-neutral structural invariants with explicit PASS/FAIL/UNKNOWN |
| MNCS-L4 | Valid repeated measurements and a predeclared useful-benefit threshold |
| MNCS-L5 | Locked regeneration, immutable evidence, holdout reevaluation, rollback, audit |

### MNCDS development profiles

| Profile | Adds |
|---|---|
| MNCDS-D1 | Controlled generation, immutable baseline, candidate identity, append-only ledger |
| MNCDS-D2 | Pinned experimentation, evidence partitions, reproducibility, repeated measurement |
| MNCDS-D3 | Predeclared selection, protected holdout, independent evaluator, MNCS binding |
| MNCDS-D4 | Release controls, tested rollback, regeneration drill, monitoring, retirement |

## Repository map

- [`spec/`](spec/MNCS-v0.2.md): normative MNCS 0.2 and draft MNCDS text.
- [`schemas/`](schemas/mncs-manifest.schema.json): machine-readable normative and experimental
  schemas.
- [`src/mncs_validator/`](src/mncs_validator/validation.py): offline validators and provider client.
- [`experimental/mnea/`](experimental/mnea/README.md): bounded Clang-backed analyzer prototype.
- [`experimental/language-evidence/`](experimental/language-evidence/README.md): C11, Rust, and
  Python profiles, providers, fixtures, and provider-conformance corpus.
- [`case-studies/`](case-studies/README.md): research implementations and evidence records.
- [`conformance-corpus/`](conformance-corpus/expected.json): deterministic validator corpus.
- [`interoperability/`](interoperability/corpus.json): cross-implementation golden vectors.
- [`docs/`](docs/index.md): documentation site.
- [`rfcs/`](rfcs/README.md): standards change process.

## Structural tools and recursive improvement

MNCS standardizes evidence semantics, not vendor names. Compiler CFG analysis, LLVM passes,
abstract interpretation, model checking, symbolic execution, proof assistants, runtime
instrumentation, language-specific verification, and independent combinations can all be
providers.

MNCDS permits evidence from one development epoch to improve an analyzer, harness, generator,
evaluator, benchmark, or search strategy in a later epoch. The changed toolchain receives a new
identity, is regression-tested, and must use uncontaminated protected evidence for any new final
claim.

## Participate

Read [CONTRIBUTING.md](CONTRIBUTING.md), [GOVERNANCE.md](GOVERNANCE.md), and the
[RFC process](rfcs/README.md). Standard changes require public review, evidence, and
consensus-seeking; no vendor has a permanent veto.

Code, schemas, and documentation are licensed under the [Apache License 2.0](LICENSE). Cite the
exact MNCS and MNCDS versions using [CITATION.cff](CITATION.cff), along with the relevant manifest,
development record, environment, and selected-candidate identities.
