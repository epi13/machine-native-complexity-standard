# Conformance manifest

`manifest.json` is the root of a claim. It identifies the MNCS and schema versions,
claimed level, component and contract, reference and machine identities, generator,
predeclared objective, acceptance policy, environment, evidence index, invariants,
complexity profile, performance results, resource bounds, provenance, limitations,
unsupported environments, regeneration, rollback, and final status.

Schema 0.1.1 separates:

- `acceptance_policy`: cumulative required gates, UNKNOWN/conflict rules,
  objective semantics, thresholds, sample counts, and regression policy;
- `gate_results`: mappings from gate names to stable evidence-index IDs; and
- computed conformance: validator report fields for each gate, claimed level,
  final result, certification eligibility, evidence used/excluded, conflicts,
  warnings, and the evidence graph.

The final status is a declared reconciliation value and MUST equal the computed
result. It is not an authoritative observation. A required gate without suitable
indexed evidence MUST NOT pass.

Core field meanings are fixed by MNCS. Extensions live under `extensions` and MUST
use a namespace-qualified key such as `example.org:energy-model`. Validators MUST
preserve unknown extension namespaces when rewriting documents, but extensions MUST
NOT change core status, gate, hash, or level semantics.
