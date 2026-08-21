# Installation

## Validator only

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
mncs version --json
mncs validate-bundle examples/minimal
```

Requires Python 3.11+.

## Family software

```bash
mncs doctor --json
mncs bootstrap --profile core --plan --json
mncs bootstrap --profile core --yes --json
```

Profiles: `core`, `developer`, `worker`, `research`, `full`. Individual
`--component` flags may be combined with a profile.

See [profiles](profiles.md) and [bootstrap](bootstrap.md).

## What installation is not

A completed install receipt records that bootstrap observed and performed
operational steps. It is not:

- MNCS or MNCDS conformance
- certification
- independent evidence
- protected custody
- governance approval
- a PASS result
- promotion authority
