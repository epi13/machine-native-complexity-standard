# Machine-Native Complexity Standard 0.1

**Status:** experimental open standard
**Version:** MNCS 0.1
**License:** Apache-2.0

## 1. Principle

Human readability is relocated, not eliminated. Humans MUST retain readable control
over meaning, limits, evidence, and lifecycle even when machines own executable
internal complexity. Machine-native complexity MUST purchase a predeclared,
measurable engineering benefit. Complexity alone is never a benefit.

## 2. Conformance

A conforming bundle MUST implement the two-layer architecture, canonical evidence
layout, manifest, content identities, explicit acceptance policy, provenance, and
claimed cumulative level defined by the linked normative modules.

The following documents are normative parts of MNCS 0.1:

1. [Normative language](normative-language.md)
2. [Scope](scope.md)
3. [Architecture](architecture.md)
4. [Conformance levels](conformance-levels.md)
5. [Evidence bundle](evidence-bundle.md)
6. [Conformance manifest](conformance-manifest.md)
7. [Invariant model](invariant-model.md)
8. [Performance evidence](performance-evidence.md)
9. [Complexity profile](complexity-profile.md)
10. [Provenance](provenance.md)
11. [Regeneration](regeneration.md)
12. [Risk and criticality](risk-and-criticality.md)
13. [Acceptance policy](acceptance-policy.md)
14. [Provider interface](provider-interface.md)
15. [Extension process](extension-process.md)

## 3. Exception-driven repair

The preferred structural workflow is:

1. Generate an immutable candidate without continuously injecting analyzer output.
2. Evaluate it independently.
3. Give no structural feedback when all required invariants PASS.
4. On FAIL, provide one compact witness and permit a bounded repair attempt.
5. On UNKNOWN, apply the declared acceptance policy.
6. Reevaluate the repaired immutable candidate from the beginning.
7. Record repair time, tokens or equivalent cost, and changed identity.
8. Record whether structural analysis found a defect runtime evaluation missed.

Example: a generated incremental parser passes differential and fuzz tests, but a
provider reports `FAIL` for `INV-EMIT-AFTER-COMMIT`, with one path from payload emit
to a state where size validation has not dominated the emit call. The policy permits
one repair. The generator receives only that witness, emits a new source hash, and
the complete behavioral, safety, structural, and performance suite runs again.
Evidence records a 42-second repair, the old and new hashes, and that runtime tests
did not detect the forbidden path. If the provider instead returns UNKNOWN because
indirect calls exceed its bound, a policy of `reject` rejects the candidate; manual
review cannot relabel the provider result.

## 4. Claim form

A public claim SHOULD state:

```text
<component> conforms to MNCS 0.1 at <level> for <environment>,
manifest sha256:<digest>, final status <PASS|FAIL|UNKNOWN>.
```

The claim MUST NOT imply accreditation, general security certification, or behavior
outside the contract and environment.
