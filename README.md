# Machine-Native Complexity Standard

[![CI](https://github.com/epi13/machine-native-complexity-standard/actions/workflows/ci.yml/badge.svg)](https://github.com/epi13/machine-native-complexity-standard/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Standard](https://img.shields.io/badge/MNCS-0.2-experimental-orange.svg)](spec/MNCS-v0.2.md)
[![Schema](https://img.shields.io/badge/schema-0.2-blue.svg)](schemas/mncs-manifest.schema.json)
[![Development specification](https://img.shields.io/badge/MNCDS-0.1--draft-purple.svg)](spec/MNCDS-v0.1-draft.md)

The Machine-Native Complexity Standard (MNCS) is an open, experimental,
community-developed, tool-neutral engineering standard for accepting generated or
machine-optimized implementations that may exceed ordinary human-maintainability
limits.

The Machine-Native Complexity Development Specification (MNCDS) is its experimental
companion for controlling how those implementations are generated, evaluated, selected,
released, regenerated, and retired. MNCS evaluates the implementation evidence; MNCDS
evaluates the development process. Neither claim implies the other.

> **Human readability is relocated, not eliminated.**

Humans retain readable specifications, contracts, limits, reference behavior,
validation policy, provenance, regeneration instructions, development controls, and
acceptance evidence. Machines may own internal execution complexity only when it
purchases a declared, measurable benefit inside an auditable correctness, safety,
resource, provenance, development, and regeneration envelope. Complexity is never a
benefit by itself.

MNCS and MNCDS are not accredited ISO, ANSI, IEEE, IETF, or similar standards. MNCS
0.2 and MNCDS 0.1-draft are intended for experimentation and public review, not as
blanket assurance claims. Validator release 0.2.0 adds portable canonical identities,
offline attestations, explicit trust, reproducible packages, and independent
implementation agreement. The experimental MNCDS validator adds offline process-record
validation without executing generators, candidates, evaluators, or evidence.

## Two complementary claims

| Claim | What it evaluates |
|---|---|
| `MNCS-L1` through `MNCS-L5` | Candidate implementation and evidence conformance |
| `MNCDS-D1` through `MNCDS-D4` | Development-process control and lifecycle assurance |

A project may state both, for example `MNCDS-D3 / MNCS-L4`, only when each result is
independently supported.

## Attested interoperability in MNCS 0.2

Evidence-derived results have RFC 8785 canonical bytes, Ed25519 DSSE-compatible
envelopes, deterministic local trust policies, reproducible `.mncs` archives, and a
versioned corpus shared with an independent Rust validator. Provider Protocol 0.1 makes
analyzers interoperable without letting normal validation launch them.

`FAIL` dominates `UNKNOWN`, which dominates `PASS`. Missing required evidence never
passes. Signature validity and trust are reported separately: a signature proves only
that a key signed bytes, not correctness, safety, performance, process discipline, or
truth.

## Install

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
mncs version
mncds version
```

For development:

```bash
python -m pip install -e '.[dev]'
make check
```

## Five-minute examples

Validate MNCS implementation evidence:

```bash
mncs validate-bundle examples/minimal
mncs certify-bundle examples/minimal
mncs summarize examples/minimal/manifest.json
mncs hash examples/minimal/machine/generated.py
mncs compare examples/minimal/manifest.json \
  examples/rejected-candidate/manifest.json
mncs pack examples/minimal --output minimal.mncs
mncs verify-package minimal.mncs
mncs key generate ./release-key.pem
```

Validate an MNCDS development process record:

```bash
mncds validate examples/mncds-d4/development-record.json
mncds validate examples/mncds-d4/development-record.json --require-pass --json
mncs schema mncds-development-record
```

Start an MNCS bundle with `mncs init my-component`. The resulting template is
intentionally incomplete: replace it with real evidence and hashes before making a
claim. MNCS and MNCDS validation are offline and never launch, import, or execute an
evidence binary, generator, candidate, analyzer, or benchmark.

## Cumulative conformance levels

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
| MNCDS-D2 | Pinned experimentation, evidence partitions, reproducibility class, repeated measurement |
| MNCDS-D3 | Predeclared selection, protected holdout, independent final evaluator, MNCS binding |
| MNCDS-D4 | Release controls, tested rollback, regeneration drill, monitoring, retirement triggers |

`UNKNOWN` never silently counts as `PASS`. Levels and profiles are cumulative within
their own families.

## CLI

### MNCS

```text
mncs init PATH
mncs validate MANIFEST
mncs validate-bundle DIRECTORY
mncs certify MANIFEST
mncs certify-bundle DIRECTORY
mncs key generate PRIVATE_PATH
mncs key inspect KEY
mncs attest STATEMENT --key PRIVATE --output ENVELOPE
mncs verify-attestation ENVELOPE --key PUBLIC_KEY
mncs trust validate-policy POLICY
mncs trust evaluate ENVELOPE POLICY
mncs pack BUNDLE --output FILE.mncs
mncs inspect-package FILE.mncs
mncs verify-package FILE.mncs
mncs unpack FILE.mncs --output DIRECTORY
mncs certify-package FILE.mncs
mncs provider inspect COMMAND
mncs provider run DESCRIPTOR REQUEST
mncs provider verify-result RESULT
mncs summarize MANIFEST
mncs compare MANIFEST_A MANIFEST_B
mncs hash PATH
mncs schema NAME
mncs version
```

### MNCDS

```text
mncds validate DEVELOPMENT_RECORD
mncds version
```

Commands support `--json`. A structurally valid MNCS bundle or MNCDS record can
truthfully produce `FAIL` or `UNKNOWN`; structural validation success does not itself
mean the candidate or process passed.

Use `--require-pass` when a non-PASS result must return exit 3. Exit 1 means invalid
evidence or record semantics, exit 2 means an operational error, and exit 3 means valid
but non-PASS under the requested policy.

Frozen MNCS schema 0.1 resources remain supported. Legacy reports set
`legacy_self_asserted_acceptance: true`; certification refuses them unless
`--allow-legacy` is explicit, and an override remains reduced-assurance. MNCDS 0.1 is
experimental and has no legacy certification path.

## Structural tools

MNCS and MNCDS standardize evidence and process semantics, not product names. Compiler
CFG analysis, LLVM passes, abstract interpretation, model checking, symbolic execution,
proof assistants, custom analyzers, runtime instrumentation, language-specific
verification, and independent combinations are all possible providers. Joern is one
optional provider and is not a normative dependency.

MNCDS explicitly permits evidence from one development epoch to improve a Joern harness,
generator, evaluator, or search strategy in the next epoch. The changed toolchain must
receive a new identity, be regression-tested, and use uncontaminated protected evidence
for any new final claim.

## Repository map

- [`spec/MNCS-v0.2.md`](spec/MNCS-v0.2.md) — normative MNCS 0.2 text
- [`spec/MNCDS-v0.1-draft.md`](spec/MNCDS-v0.1-draft.md) — draft development specification
- [`schemas/`](schemas/mncs-manifest.schema.json) — machine-readable contracts
- [`src/mncs_validator/`](src/mncs_validator/validation.py) — offline validators
- [`examples/`](examples/minimal/README.md) — accepted, rejected, repair, and MNCDS examples
- [`docs/`](docs/index.md) — documentation site
- [`rfcs/`](rfcs/README.md) — change process
- [`conformance-corpus/`](conformance-corpus/expected.json) — deterministic MNCS corpus
- [`interoperability/`](interoperability/corpus.json) — cross-language MNCS golden vectors
- [`research/`](research/graphflow-machine-native-study.md) — preliminary motivation

## Participate

Read [CONTRIBUTING.md](CONTRIBUTING.md), the [governance model](GOVERNANCE.md), and
the [RFC process](rfcs/README.md). Standard changes need public review, evidence, and
consensus-seeking; no vendor receives a permanent seat or veto.

## License and citation

Code, schemas, and documentation are licensed under the
[Apache License 2.0](LICENSE). Cite the exact MNCS and MNCDS versions using
[`CITATION.cff`](CITATION.cff); a conformance claim should also identify its manifest,
development record, and selected-candidate hashes.

A validator PASS is scoped to the declared contract, environment, evidence, policy,
identities, and process record. MNCS 0.2 and MNCDS 0.1-draft are experimental and do not
constitute accredited certification.
