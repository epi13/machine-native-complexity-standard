# Family Record Spine and MNCS Evidence Binding

Status: architecture proposal / non-normative

## Purpose

The MNCS family increasingly produces machine-readable compiler, execution, routing, evaluation, experiment and development records. MNCS should be the downstream semantic consumer of eligible evidence, not the family database or transport layer.

This document proposes how the **Family Record Spine** can funnel evidence toward MNCS while preserving producer ownership and authority boundaries.

## Core rule

> MNCS may consume exact evidence references without owning the transport, orchestration or native semantics of the systems that produced them.

Examples:

- a Fabric receipt remains an execution observation;
- a Harness role record remains actor/routing provenance;
- a Control Concept Experiment remains a coordination identity;
- a Language compiler-study record remains a compiler/language fact;
- a Forge result remains a bounded evaluator result;
- an MNCDS record remains a development-process record;
- a future MNEL or RAVEL record remains owned by that producer.

None of those records becomes an MNCS PASS merely by being attached to an assurance case.

## Progressive projection

The intended evidence flow is:

```text
compiler / execution / verifier records
        -> Concept Experiment graph
        -> scientific/adaptive interpretations when available
        -> MNCDS development record
        -> MNCS assurance case
```

Upper layers reference exact lower-layer identities rather than destructively summarizing or copying semantics.

An MNCS assurance case should therefore be able to point to the exact candidate, contract, profile, development record, evaluation results, execution cohort and unresolved evidence without requiring MNCS itself to ingest raw model conversations or every build artifact.

## Concept Reconstruction Experiments

A Concept Reconstruction Experiment (CRE) is a bounded study in which independent experimenters reconstruct a fundamental computing concept using the currently available MNCS Language semantics. The current family implementation is a source of invariants and comparison evidence rather than a transpilation template.

CRE outcomes may reveal:

- candidate implementation errors;
- language expressivity or semantic gaps;
- compiler/lowering/backend gaps;
- verifier/tooling gaps;
- portability disagreements;
- specification ambiguities;
- unresolved evidence.

These results can inform future MNCS RFC work, but experimental evidence cannot silently rewrite normative MNCS meaning.

## Binding expectations

Where an MNCS assurance case relies on records produced through the spine, the binding should preserve enough identity to determine at least:

- exact subject/candidate identity;
- MNCS specification/profile and contract identity;
- relevant MNCDS development-record identity when used;
- exact producer record identities and schema/version where material;
- evaluator/verifier identities;
- execution/environment/cohort identities;
- compatibility status;
- unresolved, conflicting or unavailable evidence;
- evidence class/claim boundary.

Missing or incompatible bindings remain `UNKNOWN` unless a stronger normative rule requires `FAIL`.

## Commons is not MNCS authority

Commons is the proposed coordination/index plane for the Family Record Spine. Commons ingestion, storage, graph traversal, lifecycle projection or bundling does not create correctness, conformance, independence, protected custody or governance authority.

MNCS validators should interpret only MNCS-owned semantics and explicitly supported external bindings.

## Temporary experiment roles

The first CREs may use ordinary models under Harness roles such as `experiment-investigator` and `adaptive-experiment-critic` while RAVEL/MNEL remain offline. Their records must preserve exact producer/model/worker identity and must not claim RAVEL/MNEL provenance.

This also creates useful future control groups: actual RAVEL/MNEL behavior can be compared against strong general models given equivalent evidence.

## Governance boundary

Evidence from CREs may motivate a standard-evolution proposal, but the path remains:

```text
observation/counterexample
 -> bounded proposal
 -> competing alternatives
 -> implementation/adversarial evidence
 -> explicit compatibility and authority analysis
 -> RFC/governance review
```

The family record spine improves traceability; it does not automate normative promotion.

## First exercise

Use a tiny study such as reconstructing the `PASS` / `UNKNOWN` / `FAIL` result lattice. Carry the exact experiment, compiler, execution and evaluator identities through Commons and an MNCDS example, then construct a bounded MNCS evidence case. The exercise should demonstrate that every layer can preserve `UNKNOWN` and disagreement without silently strengthening the claim.
