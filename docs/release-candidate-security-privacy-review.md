# MNCS 0.3 / MNCDS 0.1 internal security and privacy review

Status: internal adversarial review complete for 0.3-rc.1 / 0.1-rc.1. External
security and privacy acceptance is **OPEN**. This review cannot satisfy that gate.

| Threat | Affected requirement | Mitigation | Test evidence | Residual risk | Status | Release impact | External review |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Claim broadening | MNCS-03-RESULTS | Scope/result identities and exact root binding | mixed-result and mismatch tests | UI may omit scope | mitigated internally | external review gate | required |
| UNKNOWN promotion | Both result models | FAIL > UNKNOWN > PASS; explicit selection policy | required-UNKNOWN and unknown-promotion cases | Policy misuse outside validated records | mitigated internally | external review gate | required |
| Downgrade attack | Migration | Exact dispatch and downgrade flag | downgrade and unknown-version cases | Negotiation outside record | mitigated internally | external review gate | required |
| Identity substitution | Contract/change/lifecycle | Old/new identities and reference resolution | material-identity and replacement cases | External resolver authenticity | partial | independent review | required |
| Schema confusion | All records | Version constants, strict fields, unsupported versions | schema self-validation | Extension interpretation | mitigated internally | none internal | required |
| Canonicalization ambiguity | Inherited 0.2 | RFC 8785 and deterministic packages | existing canonicalization corpus | Numeric edge cases | partial | inherited external gate | required |
| Stale evidence and replay | Freshness | Explicit time/status/triggers | stale/fresh cases | Clock/revocation policy | partial | external policy review | required |
| Superseded evidence reuse | Lifecycle | Supersession, retirement, impact, revalidation | supersession/retirement cases | Cross-package history discovery | partial | external policy review | required |
| Dependency omission | Composition | Explicit graph and required propagation | dependency/reference cases | Producer can omit a real dependency | residual high | contract/reviewer gate | required |
| Correlated failure concealment | Composition | Shared evidence and correlation groups | correlated/shared-evidence cases | Undeclared common cause | residual moderate | reviewer gate | required |
| False independence | MNCDS roles | Separate implementation/operator/organization facts | Rust report and D3/D4 UNKNOWN | False declarations need audit | residual moderate | external evidence gate | required |
| False protected custody | MNCDS partitions | Custody class, access, contamination | protected-evidence cases and study | Off-record access | residual moderate | external evidence gate | required |
| Holdout contamination | MNCDS D3/D4 | Partition identities and contamination failure | holdout-contamination case | Off-record access | residual moderate | external audit gate | required |
| Evaluator/threshold mutation | MNCDS authority | Forbidden permissions and epoch identities | mutation cases | Off-record mutation | residual moderate | independent review | required |
| Selective reporting | Ledger/measurement | Material retention; best-run-only FAIL | retention/measurement cases | Undisclosed candidates | residual moderate | external audit gate | required |
| Result collapse | Combined assurance | Separate objects and checked label | attempted-collapse case | Nonconforming UI | mitigated internally | none internal | required |
| Malicious recursive references | Graphs/lineage | Existence and cycle checks | dependency/candidate/epoch cycles | Large acyclic graphs | resource policy | resource review | required |
| Resource exhaustion | Validators | Offline parsing and caller limits | corpus/package-limit tests | Universal maxima are not portable | partial | known limitation | required |
| Path traversal / unsafe resolution | Offline/package | Existing secure package rules | malicious-archive tests | New external resolvers | mitigated locally | none internal | required |
| Implicit network or execution | Validation boundary | No provider/candidate execution | CLI/corpus source and tests | Host wrappers | mitigated internally | none internal | required |
| Malicious archives | Packages | Entry/path/size validation | inherited package tests | Library defects | partial | inherited external gate | required |
| Redaction as verification | Both | Hidden required facts remain UNKNOWN | specifications/UNKNOWN cases | Future proof profiles | mitigated internally | none internal | required |
| Private-data leakage | Evidence | Minimize data; opaque IDs; privacy impact | schema review | Relationship metadata | residual moderate | privacy review gate | required |
| Misleading disposition | Assurance | Disposition has no conformance status | operational-review case | UI misuse | mitigated internally | none internal | required |

No confirmed path traversal, implicit network access, implicit provider execution, or
candidate execution was found in new ordinary validation paths. Confirmed logic
defects found during review—UNKNOWN overwriting FAIL and incomplete root-MNCDS
binding—were corrected and covered by corpus agreement.
