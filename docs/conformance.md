# Conformance

MNCS and MNCDS define separate cumulative conformance families.

## MNCS implementation levels

1. **MNCS-L1** establishes behavioral conformance.
2. **MNCS-L2** adds safety and resource enforcement.
3. **MNCS-L3** adds provider-neutral structural invariants.
4. **MNCS-L4** adds valid comparative measurement and useful benefit.
5. **MNCS-L5** adds locked regeneration, holdout, immutable audit, and rollback.

Every required gate is PASS, FAIL, or UNKNOWN. FAIL defeats the claim. UNKNOWN keeps its
identity and prevents PASS. A valid manifest with final status FAIL is useful: it is a
trustworthy rejection record, not a conforming accepted implementation.

For schemas 0.1.1 and 0.2, conformance is computed from indexed observations. Policy
declares required gates; it does not declare observed PASS. Every cumulative gate must
have suitable evidence bound to the candidate and contract. The validator emits PASS,
FAIL, or UNKNOWN per gate and for the claimed level, then checks that the manifest's final
status matches.

Validation can succeed for an honest FAIL or UNKNOWN. Certification additionally
requires an evidence-derived PASS.

See the [MNCS normative specification](specification.md).

## MNCDS development profiles

1. **MNCDS-D1** establishes controlled generation, baseline lock, candidate identity,
   lineage, and an auditable ledger.
2. **MNCDS-D2** adds pinned experimentation, evidence partitions, reproducibility class,
   repeated measurement, and evaluator regression corpora.
3. **MNCDS-D3** adds predeclared selection, protected holdout, independent final
   evaluation, role-conflict checks, and MNCS binding when applicable.
4. **MNCDS-D4** adds release controls, monitoring, tested rollback, a regeneration or
   replacement drill, and retirement triggers.

An MNCDS record may be structurally valid while computing FAIL or UNKNOWN. UNKNOWN must
not be promoted to PASS by human review; explicit review may preserve an overall UNKNOWN
for an experimental process record.

See the [MNCDS guide](mncds.md) and [draft specification](mncds-specification.md).

## Combined claims

A project may publish both results in the form:

```text
MNCDS-D3 / MNCS-L4
```

The statuses, versions, identities, scopes, and issue sets remain separate. An MNCDS PASS
does not prove implementation correctness, and an MNCS PASS does not prove disciplined
development.
