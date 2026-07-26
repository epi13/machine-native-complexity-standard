# Conformance

Levels are cumulative:

1. **MNCS-L1** establishes behavioral conformance.
2. **MNCS-L2** adds safety and resource enforcement.
3. **MNCS-L3** adds provider-neutral structural invariants.
4. **MNCS-L4** adds valid comparative measurement and useful benefit.
5. **MNCS-L5** adds locked regeneration, holdout, immutable audit, and rollback.

Every required gate is PASS, FAIL, or UNKNOWN. FAIL defeats the claim. UNKNOWN keeps
its identity and prevents PASS. A valid manifest with final status FAIL is useful:
it is a trustworthy rejection record, not a conforming accepted implementation.

See the [normative specification](specification.md).
For schemas 0.1.1 and 0.2, conformance is computed from indexed observations. Policy declares
required gates; it does not declare observed PASS. Every cumulative gate must have
suitable evidence bound to the candidate and contract. The validator emits PASS,
FAIL, or UNKNOWN per gate and for the claimed level, then checks that the manifest's
final status matches.

Validation can succeed for an honest FAIL or UNKNOWN. Certification additionally
requires an evidence-derived PASS.
