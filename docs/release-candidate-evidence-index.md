# Release-candidate evidence index

| Evidence | Location | Internal result | External status |
| --- | --- | --- | --- |
| MNCS 0.3 specification | `spec/MNCS-v0.3-rc.1.md` | reviewable | approval OPEN |
| MNCDS 0.1 specification | `spec/MNCDS-v0.1-rc.1.md` | reviewable | approval OPEN |
| Architecture decisions | `spec/MNCS-v0.3-MNCDS-v0.1-decisions.md` | resolved locally | RFC approval OPEN |
| Normative schemas | `schemas/*-0.3.schema.json`, `schemas/mncds-development-record-0.1.schema.json` | self-validating | freeze review OPEN |
| Python consumer | `src/mncs_validator/assurance/`, `mncds.py` | modular semantic implementation; corpus agreement | external operation OPEN |
| Rust consumer | `independent/rc-consumer` | 74/74 corpus agreement plus bounded package, DSSE/Ed25519, and trust-policy cross-checks | operator/organization UNKNOWN |
| Golden corpus | `conformance/release-candidate/corpus.json` | 74/74 both consumers, including transitive impact | independent freeze OPEN |
| Two-epoch study | [mncs-reference-studies recursive analyzer](https://github.com/epi13/mncs-reference-studies/tree/main/studies/recursive-analyzer) | internal selection PASS; MNCS UNKNOWN | custody/independence UNKNOWN |
| Migration model | `docs/migration-0.2-to-0.3-mncds-0.1.md` | implemented | compatibility review OPEN |
| Security/privacy review | `docs/release-candidate-security-privacy-review.md` | internal complete | external acceptance OPEN |
| Gap matrix | `docs/release-gap-matrix.json` | machine-readable | blockers explicit |
| Governance/checklists | `GOVERNANCE.md`, `docs/release-readiness-checklists.md` | reviewable | named authorities OPEN |

Readiness dimensions:

- implementation readiness: internally testable;
- evidence readiness: internal corpus/study complete, external evidence incomplete;
- independent-review readiness: package prepared;
- governance readiness: procedures prepared, required actors OPEN;
- final release authorization: **not permitted**.
