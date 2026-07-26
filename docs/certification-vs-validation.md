# Certification versus validation

Validation and certification answer different questions.

`mncs validate MANIFEST` and `mncs validate-bundle DIRECTORY` check schema,
semantics, hashes, bindings, evidence graph, computed gates, and final-status
reconciliation. Exit 0 means the bundle is valid even when its honest computed
status is FAIL or UNKNOWN.

`mncs certify` and `mncs certify-bundle` require the same validity plus a
certification-eligible computed PASS. `--require-pass` gives validation commands
the same PASS requirement.

Exit codes are:

| Code | Meaning |
|---|---|
| 0 | Valid; and when PASS is required, certification-eligible PASS |
| 1 | Structurally or semantically invalid |
| 2 | CLI, filesystem, or operational error |
| 3 | Valid FAIL/UNKNOWN, or legacy self-asserted input, when PASS is required |

Schema 0.1 legacy PASS is not evidence-derived. `--allow-legacy` can override the
certification refusal, but the report records the override and reduced assurance.

Certification is local validator terminology, not accreditation. It covers only
the declared contract, candidate identity, evaluator evidence, and environment.
