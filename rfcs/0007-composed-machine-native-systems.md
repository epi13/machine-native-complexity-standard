# RFC 0007: Experimental composed machine-native systems

Status: Draft

This RFC proposes non-normative boundary contracts, composed assurance records, and measured evidence epochs. It does not change MNCS 0.2 or promote MNCDS 0.1-draft.

Composition retains component and boundary claims, binds every provider and environment, and applies `FAIL > UNKNOWN > PASS`. Missing required evidence is UNKNOWN. `REVIEW_REQUIRED` is an experimental workflow disposition, not an MNCS PASS.

## Wave Three amendment

Wave Three adds an experimental composed-evidence-epoch schema and a recovery-focused C11/Go/Rust implementation. An epoch records preregistration, evidence partitions, identities, strict builds, generated-binding regeneration, checkpoint and replacement drills, mutation artifacts, repeated measurements, evaluator status, cross-host status, formal claim status, and known limitations.

The amendment does not permit a system PASS when a required component, boundary, recovery drill, mutation campaign, or environment remains UNKNOWN. Public CI evidence is not a protected holdout. A second implementation maintained in the same repository is not organizationally independent.

A successful regeneration and readable replacement drill can support only a narrow D4-related subclaim. Full MNCDS-D4 remains UNKNOWN without controlled release, production monitoring, retirement controls, independent witnessing, and retained evidence custody.
