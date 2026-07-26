# Validator

`mncs-validator` is the reference offline validator. It:

- validates Draft 2020-12 schemas;
- confines relative references to the bundle;
- verifies local SHA-256 identities;
- detects missing and stale evidence;
- derives cumulative gates and checks final-status reconciliation;
- verifies evaluator, environment, provenance, and performance bindings;
- reports the evidence dependency graph and legacy assurance state;
- validates canonical layout; and
- performs compatibility-gated Pareto comparison.
- canonicalizes RFC 8785 JSON and verifies Ed25519 attestations;
- evaluates deterministic trust without hidden roots;
- creates and verifies reproducible `.mncs` packages; and
- explicitly runs bounded Provider Protocol 0.1 commands only when requested.

It never imports or executes a referenced source file, script, binary, or provider.
Use `--json` on commands for automation.

`validate` and `validate-bundle` return 0 for a valid PASS, FAIL, or UNKNOWN.
`certify`, `certify-bundle`, and `--require-pass` additionally require a computed
eligible PASS. Exit 1 means invalid, exit 2 operational error, and exit 3 valid but
not eligible for the requested PASS. Legacy 0.1 certification requires
`--allow-legacy` and remains visibly reduced-assurance.

The independent `mncs-rs` binary supports the interoperable validation subset and
shares the versioned golden corpus. Neither implementation executes evidence.
