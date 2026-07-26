# Machine-Native Complexity Standard

[![CI](https://github.com/epi13/machine-native-complexity-standard/actions/workflows/ci.yml/badge.svg)](https://github.com/epi13/machine-native-complexity-standard/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Standard](https://img.shields.io/badge/MNCS-0.1-experimental-orange.svg)](spec/MNCS-v0.1.md)

The Machine-Native Complexity Standard (MNCS) is an open, experimental,
community-developed, tool-neutral engineering standard for accepting generated or
machine-optimized implementations that may exceed ordinary human-maintainability
limits.

> **Human readability is relocated, not eliminated.**

Humans retain readable specifications, contracts, limits, reference behavior,
validation policy, provenance, regeneration instructions, and acceptance evidence.
Machines may own internal execution complexity only when it purchases a declared,
measurable benefit inside an auditable correctness, safety, resource, provenance,
and regeneration envelope. Complexity is never a benefit by itself.

MNCS is not an accredited ISO, ANSI, IEEE, IETF, or similar standard. Version 0.1 is
intended for experimentation and public review, not as a blanket assurance claim.

## Install

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
mncs version
```

For development:

```bash
python -m pip install -e '.[dev]'
make check
```

## Five-minute example

```bash
mncs validate-bundle examples/minimal
mncs summarize examples/minimal/manifest.json
mncs hash examples/minimal/machine/generated.py
mncs compare examples/minimal/manifest.json \
  examples/rejected-candidate/manifest.json
```

Start a bundle with `mncs init my-component`. The resulting template is intentionally
incomplete: replace it with real evidence and hashes before making a claim. Validation
is offline and never launches, imports, or executes an evidence binary.

## Cumulative conformance levels

| Level | Adds |
|---|---|
| MNCS-L1 | Behavioral conformance, readable contract/reference, edge cases, strict tools |
| MNCS-L2 | Runtime and memory safety, malformed inputs, fuzz/property tests, resource limits |
| MNCS-L3 | Tool-neutral structural invariants with explicit PASS/FAIL/UNKNOWN |
| MNCS-L4 | Valid repeated measurements and a predeclared useful-benefit threshold |
| MNCS-L5 | Locked regeneration, immutable evidence, holdout reevaluation, rollback, audit |

`UNKNOWN` never silently counts as `PASS`. Levels are cumulative; claiming L4 means
satisfying L1 through L4.

## CLI

```text
mncs init PATH
mncs validate MANIFEST
mncs validate-bundle DIRECTORY
mncs summarize MANIFEST
mncs compare MANIFEST_A MANIFEST_B
mncs hash PATH
mncs schema NAME
mncs version
```

Commands support `--json`. A structurally valid bundle can truthfully declare a
candidate `FAIL`; validation success means its evidence is internally consistent,
not that the candidate passed.

## Structural tools

MNCS standardizes evidence semantics, not product names. Compiler CFG analysis, LLVM
passes, abstract interpretation, model checking, symbolic execution, proof
assistants, custom analyzers, runtime instrumentation, language-specific verification,
and independent combinations are all possible providers. Joern is one optional
provider and is not a normative dependency.

## Repository map

- [`spec/`](spec/MNCS-v0.1.md) — normative MNCS 0.1 text
- [`schemas/`](schemas/mncs-manifest.schema.json) — machine-readable contracts
- [`src/mncs_validator/`](src/mncs_validator/validation.py) — offline validator
- [`examples/`](examples/minimal/README.md) — accepted, rejected, and repair bundles
- [`docs/`](docs/index.md) — documentation site
- [`rfcs/`](rfcs/README.md) — change process
- [`research/`](research/graphflow-machine-native-study.md) — preliminary motivation

## Participate

Read [CONTRIBUTING.md](CONTRIBUTING.md), the [governance model](GOVERNANCE.md), and
the [RFC process](rfcs/README.md). Standard changes need public review, evidence,
and consensus-seeking; no vendor receives a permanent seat or veto.

## License and citation

Code, schemas, and documentation are licensed under the
[Apache License 2.0](LICENSE). Cite the exact MNCS version using
[`CITATION.cff`](CITATION.cff); a conformance claim should also identify its manifest
hash.
