# Release-candidate migration and version negotiation

This compatibility model covers MNCS 0.1, 0.1.1, 0.2, and 0.3-rc.1 plus
MNCDS 0.1-draft and 0.1-rc.1. Migration is always explicit and never rewrites the
source claim.

| Input | Dispatch | Permitted relationship to an RC case |
| --- | --- | --- |
| MNCS schema 0.1 / standard 0.1 | Frozen legacy validator | Historical claim only |
| MNCS schema 0.1.1 / standard 0.1 | Frozen evidence-derived validator | Historical claim or referenced component |
| MNCS schema 0.2 / standard 0.2 | Current stable validator | Historical claim, referenced component, or wrapped package retaining 0.2 result |
| MNCS 0.3-rc.1 record | Exact record-kind dispatch | New release-candidate claim |
| MNCDS 0.1-draft | Frozen draft dispatch | Historical development result |
| MNCDS 0.1-rc.1 | Exact aggregate dispatch | New release-candidate development result |
| Unknown version | `UNSUPPORTED` | Never PASS; no fallback |

`mncs version --json` exposes stable and release-candidate versions. `mncs schema
NAME` discovers every bundled schema. `mncs migration-inspect FILE` reports dispatch
without changing bytes or identities.

## MNCS 0.2 to 0.3-rc.1

Three paths are valid:

1. Retain the 0.2 claim unchanged.
2. Reference the 0.2 claim as a mixed-version component in a 0.3 assurance case.
3. Reevaluate contract adequacy, implementation evidence, dependency closure,
   freshness, and lifecycle rules to create a new 0.3 claim identity.

Wrapping a 0.2 bundle does not promote its result. A downgrade is present when policy
requires 0.3 but a producer substitutes 0.2. Canonical JSON and content identities
retain their 0.2 meaning; new or materially changed records get new identities.
Existing attestations continue to attest their original predicate. A new attestation
must bind the 0.3 predicate and schema version. Provider Protocol 0.1 remains a separate
explicit execution boundary.

Example migration metadata for a wrapper:

```json
{
  "source_family": "MNCS",
  "source_version": "0.2",
  "source_identity": "result.component-v1",
  "mode": "wrapped",
  "downgrade_detected": false,
  "historical_facts_status": "UNKNOWN"
}
```

`historical_facts_status` is `UNKNOWN` because wrapping cannot manufacture facts that
were not recorded under 0.2.

## MNCDS draft to 0.1-rc.1

The draft record stays valid as a draft. An RC representation starts at the oldest
reliable baseline and creates a new record identity. It records normalized charter,
environment, authority, partitions, protected evidence, evaluator, candidate,
selection, epoch, MNCS binding, and lifecycle facts. Missing historical facts remain
`UNKNOWN`; they are not reconstructed from current practice. Candidate and epoch
lineage may reference only identities that can be supported.

## Corpus and package compatibility

The legacy MNCS and MNCDS corpora remain versioned and unchanged. The RC corpus is an
additional direct-consumer corpus. Existing `.mncs` package integrity, archive safety,
and attestation rules are inherited. An RC offline resolution set may contain a 0.2
package, but the assurance case preserves the embedded 0.2 result and separately
records its 0.3 composition consequences.
