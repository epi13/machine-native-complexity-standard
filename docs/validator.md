# Validators

The `mncs-validator` package exposes two separate offline command families.

## MNCS validator

`mncs` validates implementation evidence. It:

- validates Draft 2020-12 schemas;
- confines relative references to the bundle;
- verifies local SHA-256 identities;
- detects missing and stale evidence;
- derives cumulative gates and checks final-status reconciliation;
- verifies evaluator, environment, provenance, and performance bindings;
- reports the evidence dependency graph and legacy assurance state;
- validates canonical layout and performs compatibility-gated Pareto comparison;
- canonicalizes RFC 8785 JSON and verifies Ed25519 attestations;
- evaluates deterministic trust without hidden roots;
- creates and verifies reproducible `.mncs` packages; and
- explicitly runs bounded Provider Protocol 0.1 commands only when requested.

The independent `mncs-rs` binary supports the interoperable validation subset and shares
the versioned golden corpus.

## MNCDS validator

`mncds` validates development-process records. It checks:

- aggregate development-record schema conformance;
- required roles and duplicate role bindings;
- forbidden generator authority;
- evidence-partition overlap and holdout contamination;
- candidate identities, parent references, and lineage cycles;
- selection-policy and selected-candidate consistency;
- required FAIL and UNKNOWN treatment;
- D2 reproducibility and evaluator regression-corpus requirements;
- D3 protected holdout, predeclared selection, evaluator authority and executable
  separation, reviewer binding, and independent selected-candidate evidence;
- agreement between MNCDS and MNCS candidate, contract, and environment identities; and
- D4 rollback and regeneration-drill outcomes.

The MNCDS validator is experimental. A second independent implementation must agree on
the versioned MNCDS corpus before RFC 0004 can satisfy its acceptance gate.

## Safety and exit behavior

Neither command imports or executes a referenced source file, generator, candidate,
script, binary, evaluator, benchmark, evidence object, or provider during ordinary
validation. Provider execution occurs only through an explicit MNCS provider command.

Use `--json` for automation.

Validation returns 0 for a structurally valid PASS, FAIL, or UNKNOWN unless
`--require-pass` is supplied. Exit 1 means invalid evidence or record semantics, exit 2
means operational error, and exit 3 means valid but non-PASS for the requested operation.
Legacy MNCS 0.1 certification requires `--allow-legacy` and remains visibly
reduced-assurance. MNCDS has no legacy certification override.
