# Experimental Machine-Native Evidence Analyzer

This directory contains the first bounded in-house analyzer prototype proposed by RFC
0005. It is an example Provider Protocol 0.1 implementation, not a normative dependency
or production verifier.

The current provider analyzes one C11 translation unit with Clang AST JSON and supports a
small invariant vocabulary. Unsupported semantics remain UNKNOWN.

Inspect capabilities:

```bash
mncs provider inspect python experimental/mnea/clang_provider.py --json
```

Run an explicit request:

```bash
mncs provider run descriptor.json request.json --json
```

See `docs/machine-native-evidence-analyzer.md` for request shape, limitations, evidence
semantics, and the two-epoch study design.
