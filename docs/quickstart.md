# Quickstart

Create an isolated environment and install the validator:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
mncs version
```

Validate and inspect the smallest complete bundle:

```bash
mncs validate-bundle examples/minimal
mncs summarize examples/minimal/manifest.json
mncs validate examples/minimal/manifest.json --json
```

Start your own:

```bash
mncs init component-bundle
mncs hash component-bundle/reference/reference.py
mncs schema manifest
```

`init` produces an explicitly incomplete template. Add real evidence, compute every
hash after files are immutable, and validate the complete directory.
