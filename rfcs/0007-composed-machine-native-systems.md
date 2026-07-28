# RFC 0007: Experimental composed machine-native systems

Status: Draft

This RFC proposes non-normative boundary contracts, composed assurance records, measured composition epochs, evidence-custody records, cross-host agreement, and claim-readiness semantics. It does not change MNCS 0.2 or promote MNCDS 0.1-draft.

Composition retains component and boundary claims, binds every provider and environment, and applies `FAIL > UNKNOWN > PASS`. Missing required evidence is UNKNOWN. `REVIEW_REQUIRED` is an experimental workflow disposition, not an MNCS PASS.

Wave Four adds three experimental record families:

1. **Evidence custody** binds preregistration, candidate freeze, protected corpus, raw output, normalized output, actors, attestations, and disclosure order. It prohibits development evidence from being relabeled as protected.
2. **Cross-host agreement** reconciles distinct host records by contract, epoch, component, tool, and semantic identities. Identity or output mismatch fails; unavailable required gates remain unknown.
3. **Claim readiness** evaluates MNCS implementation and MNCDS lifecycle inputs separately. Promotion requires both formal results and release authorization to pass.

The reference tools validate structural separation but cannot prove organizational independence. A developer-controlled repository cannot act as its own protected corpus custodian, independent evaluator, or independent witness merely by running separate processes.

The new loopback service boundary is evidence for one bounded local HTTP contract only. It does not broaden the native or process boundary claims and does not establish general distributed-system correctness.

Full MNCDS-D4 remains unclaimed until release approval, operational monitoring, rollback thresholds, retirement controls, protected evidence custody, and an independently witnessed replacement drill are actually performed and retained.
