# RFC 0007: Experimental composed machine-native systems

Status: Draft

This RFC proposes non-normative boundary contracts, composed assurance records, measured composition epochs, evidence-custody records, cross-host agreement, claim-readiness semantics, and portable reproduction cohorts. It does not change MNCS 0.2 or promote MNCDS 0.1-draft.

Composition retains component, boundary, host, and cohort claims, binds every provider and environment, and applies `FAIL > UNKNOWN > PASS`. Missing required evidence is UNKNOWN. `REVIEW_REQUIRED` is an experimental workflow disposition, not an MNCS PASS.

Wave Four added evidence custody, cross-host agreement, and separate MNCS and MNCDS claim readiness. The reference tools validate structural separation but cannot prove organizational independence.

Wave Five adds three experimental record families:

1. **Portable evaluation bundle** binds a frozen candidate, evaluator, workload, file identities, minimum runtime, entrypoint, network policy, and claim boundary.
2. **Host execution record** binds one machine label, operator, environment, bundle identity, integrity and semantic gates, optional toolchain capabilities, raw artifact identity, and explicit independence and holdout statuses.
3. **Reproduction cohort** reconciles host records under a preregistered machine plan and classifies single-host, operator-controlled, multi-operator public, or independently attested reproduction without conflating them.

A same-operator five-machine cohort can establish meaningful public reproduction when the records cover the declared Windows, Fedora, and Raspberry Pi OS machines and agree under one frozen bundle. It cannot establish protected holdout or independent evaluation merely because the physical machines differ.

The portable evaluator uses no third-party runtime dependencies and requires no network access. Its PASS is limited to the bundled semantic, checkpoint, corruption, and environment contract; it does not replace the full C11/Go/Rust evidence epoch.

Full MNCDS-D4 remains unclaimed until release approval, operational monitoring, rollback thresholds, retirement controls, protected evidence custody, and an independently witnessed replacement drill are actually performed and retained.
