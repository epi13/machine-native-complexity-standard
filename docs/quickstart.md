# Quickstart

This page validates MNCS evidence. To discover or install the wider family, see
[Getting started](getting-started.md) and [Bootstrap](bootstrap.md).

Create an isolated environment and install the validators:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
mncs version
mncds version
```

## Validate implementation evidence

Validate and inspect the smallest complete MNCS bundle:

```bash
mncs validate-bundle examples/minimal
mncs summarize examples/minimal/manifest.json
mncs validate examples/minimal/manifest.json --json
```

Start your own MNCS bundle:

```bash
mncs init component-bundle
mncs hash component-bundle/reference/reference.py
mncs schema manifest
```

`mncs init` produces an explicitly incomplete template. Add real evidence, compute every
hash after files are immutable, and validate the complete directory.

## Validate development-process evidence

Validate the cumulative MNCDS-D4 reference record:

```bash
mncds validate examples/mncds-d4/development-record.json
mncds validate examples/mncds-d4/development-record.json --require-pass --json
mncs schema mncds-development-record
mncs schema contract-profile-0.3
mncs schema assurance-case-0.3
mncs validate-record assurance examples/release-candidate-0.3/assurance-case.json
mncds validate examples/mncds-0.1-rc/development-record.json --json
mncs corpus release-candidate --json
```

MNCS and MNCDS produce separate results. An implementation PASS does not establish that
the development process followed MNCDS, and a process PASS does not establish that the
selected implementation satisfies MNCS.

Both validators operate offline and do not execute referenced generators, candidates,
evaluators, analyzers, benchmarks, source files, or binaries.
