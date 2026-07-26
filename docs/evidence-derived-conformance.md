# Evidence-derived conformance

Schema 0.1.1 no longer asks a manifest producer to author authoritative PASS
statuses in acceptance policy. The producer declares requirements and supplies
stable evidence-index IDs:

```json
{
  "acceptance_policy": {
    "required_gates": ["behavioral", "compiler_matrix"],
    "on_unknown": "reject",
    "conflicting_evidence": "reject"
  },
  "gate_results": {
    "behavioral": ["gate-behavioral"],
    "compiler_matrix": ["gate-compiler_matrix"]
  }
}
```

The validator loads the indexed records without executing them, checks their
content hashes and identity bindings, derives gate statuses, and emits an evidence
graph. A required gate with no usable evidence derives UNKNOWN and invalidates the
bundle. Conflicting observations are explicit. Aggregation is deterministic:
FAIL, then UNKNOWN, then PASS.

General gate results bind the contract, candidate and optional reference source,
component identity, evaluator identity record, environment identity record,
timestamps, observation counts, supporting evidence, assumptions, and limitations.
PASS requires positive observations and supporting references; FAIL carries a
witness; UNKNOWN carries a reason.

Performance observations are bound more deeply and produce three validator-derived
gates: measurement validity, useful benefit, and worst regression. Identity hashes
without indexed identity records do not satisfy the binding model.

The final manifest status is a reconciliation field. It must equal the validator's
computed result; it is not an input to acceptance.

MNCS 0.1 remains experimental. A PASS is scoped to the indexed contract and
environment and does not create an accredited certification.
