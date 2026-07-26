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
