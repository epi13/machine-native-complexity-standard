# MNCS 0.3 / MNCDS 0.1 release-gap matrix

The authoritative machine-readable matrix is
[`release-gap-matrix.json`](release-gap-matrix.json). It separates completed local
implementation work from evidence that code cannot manufacture.

| Area | Local state | Remaining gate | Classification |
| --- | --- | --- | --- |
| MNCS results, contracts, composition, lifecycle, migration | Implemented in schemas, Python, Rust, and corpus | RFC 0005 review and approval | `GOVERNANCE_BLOCKER` |
| Inherited identity, package, trust, and attestation rules | Python and existing independent Rust coverage retained | Independent review of inheritance into 0.3 | `INDEPENDENT_IMPLEMENTATION_BLOCKER` |
| MNCS freshness and graph-impact generality | Python complete for RC semantics; Rust covers all golden vectors | Broader independent implementation evidence | `INDEPENDENT_IMPLEMENTATION_BLOCKER` |
| MNCDS aggregate, D1-D4, authority, ledger, selection, lifecycle | Implemented in schema, Python, Rust, and corpus | RFC 0004 review and approval | `GOVERNANCE_BLOCKER` |
| Independent operator and organizational independence | Explicitly `UNKNOWN` | Evidence from an external actor | `EXTERNAL_EVIDENCE_BLOCKER` |
| Protected custody | Developer-withheld study evidence only | Externally controlled custody/evaluation | `EXTERNAL_EVIDENCE_BLOCKER` |
| Security and privacy | Structured internal review and regressions | External acceptance | `SECURITY_OR_PRIVACY_BLOCKER` |
| Final authorization | Checklists and evidence index prepared | Named approvals, signing authority, and release authority | `GOVERNANCE_BLOCKER` |

No Wave Six or optional broad case study is a release blocker. Open ecosystem issues
remain optional post-release profiles unless governance reclassifies them.
