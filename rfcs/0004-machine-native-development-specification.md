# RFC 0004: Machine-Native Complexity Development Specification

- Status: Draft
- Authors: Alexander Collamore
- Created: 2026-07-26
- Review deadline: 2026-08-09
- Target version: MNCS 0.3 (proposed)
- Conflicts disclosed: Repository owner and proposal author are the same person; independent review is required before acceptance.

## Summary

This RFC proposes the **Machine-Native Complexity Development Specification (MNCDS)** as a normative companion to MNCS.

MNCS defines the evidence and acceptance envelope for machine-native implementations. MNCDS defines the development lifecycle that produces a candidate for that envelope: problem declaration, baseline capture, candidate generation, constrained search, evaluation, selection, independent verification, release, monitoring, regeneration, and retirement.

The central rule is:

> A machine-native implementation may be difficult for humans to maintain internally, but the process that creates, selects, validates, reproduces, and replaces it must remain explicit, bounded, inspectable, and reversible.

MNCDS does not prescribe a model, optimizer, programming language, analyzer, search algorithm, or development platform. It standardizes the control surfaces and records needed to distinguish disciplined machine-native development from unbounded code generation or unverifiable optimization.

## Motivation

MNCS 0.2 establishes evidence-derived conformance, reproducible packages, provider interoperability, explicit trust, and scoped certification. Those mechanisms answer whether a submitted implementation is supported by adequate evidence inside a declared contract and environment.

They do not fully answer how the implementation was produced.

A development process can satisfy an output test while still being poorly controlled. Examples include:

- repeatedly tuning against the final acceptance suite until it becomes training data;
- changing the objective after seeing candidate results;
- selecting a candidate without preserving rejected alternatives or the selection rationale;
- accepting an apparent performance gain caused by noise, environment drift, or a weakened baseline;
- using an analyzer whose failures are silently treated as absence of defects;
- allowing a generator to modify the contract, reference implementation, evaluator, or threshold it is supposed to satisfy;
- losing prompts, model identity, seeds, toolchain, datasets, or search history needed to reproduce or replace a candidate;
- deploying a machine-native artifact without rollback, regeneration, monitoring, or retirement controls.

A standard for machine-native complexity therefore needs two distinct but connected layers:

1. **MNCS:** what evidence is required to accept a candidate.
2. **MNCDS:** what controls are required while developing and selecting that candidate.

This separation preserves tool neutrality and prevents historical MNCS bundles from becoming retroactively invalid because their development histories were not recorded.

## Normative proposal

The proposed normative text consists of:

- `spec/MNCDS-v0.1-draft.md` — lifecycle and profile requirements;
- `spec/MNCDS-v0.1-records-and-decisions.md` — initial interoperable record, stochastic reproducibility, evaluator independence, rejected-candidate retention, privacy-extension, and reporting semantics.

MNCDS defines ten lifecycle stages:

1. Development charter
2. Baseline and environment lock
3. Evaluation partitioning
4. Candidate-generation envelope
5. Search and experiment ledger
6. Progressive evaluation
7. Candidate selection
8. Independent verification
9. Release and operational controls
10. Regeneration, replacement, and retirement

### Core requirements

A conforming MNCDS process MUST:

- bind development to a readable contract, threat model, resource envelope, and declared useful-benefit objective;
- preserve an immutable baseline before candidate search begins;
- separate development evidence from selection and protected-holdout evidence;
- prevent the candidate generator from silently changing the contract, evaluator, reference behavior, threshold, or acceptance policy;
- record each materially evaluated candidate and its lineage in an append-only experiment ledger;
- report evaluator and analyzer outcomes as PASS, FAIL, or UNKNOWN without converting missing or unsupported analysis into PASS;
- predeclare the candidate-selection rule before final holdout evaluation;
- preserve rejected candidates or auditable aggregates under the rules in the records module;
- require independent verification of the selected candidate against fresh or previously inaccessible evidence for D3 and above;
- produce an MNCS bundle for any MNCS conformance claim;
- define rollback, regeneration, monitoring, and retirement conditions before deployment.

### Development conformance profiles

Profiles are cumulative:

- **MNCDS-D1 — Controlled generation:** charter, baseline, bounded generator authority, candidate identity, lineage, and basic ledger.
- **MNCDS-D2 — Reproducible experimentation:** pinned environment, evaluation partitions, declared reproducibility class, repeated measurement, and evaluator regression corpus.
- **MNCDS-D3 — Independent selection:** predeclared selection policy, protected holdout, independent final evaluator, explicit UNKNOWN treatment, and MNCS binding when applicable.
- **MNCDS-D4 — Operational regeneration:** release binding, rollback triggers, monitoring, regeneration drill, and retirement records.

These profiles describe development-process assurance and MUST NOT substitute for MNCS conformance levels. A project may state both, for example `MNCDS-D3 / MNCS-L4`, provided each claim is independently supported.

### Separation of authority

MNCDS distinguishes:

- contract authority;
- generator authority;
- evaluator authority;
- selection authority;
- release authority;
- independent reviewer.

One person or system MAY hold multiple roles in small experiments, but overlap MUST be disclosed. For D3 and above, the final evaluator MUST use authority and executable identities distinct from the generator and MUST be bound to the independent-reviewer role.

Identity separation demonstrates a declared control boundary. It does not prove honesty, competence, or absence of collusion.

### Recursive improvement

MNCDS explicitly permits generated evidence to improve a generator, harness, analyzer, or search strategy, including using alternative implementations to improve a Joern-based harness.

Recursive improvement MUST preserve epoch boundaries:

- evidence from epoch `n` MAY inform tools and search policy in epoch `n+1`;
- the updated toolchain MUST receive a new identity and version;
- protected holdout evidence from epoch `n` MUST NOT silently become development evidence for the same acceptance claim;
- prior claims remain bound to their old toolchain and evidence identities;
- a materially changed harness MUST be revalidated against its regression or conformance corpus;
- unresolved disagreement cases MUST remain UNKNOWN rather than being forced into agreement.

## Experimental schema and validator

The first implementation uses one aggregate, additive schema:

- `schemas/mncds-development-record.schema.json`

The installed validator exposes the same schema through:

```text
mncs schema mncds-development-record
```

The separate process validator is:

```text
mncds validate DEVELOPMENT_RECORD
```

The validator performs offline schema and cross-record semantic checks. It MUST NOT execute or import generators, candidates, analyzers, evaluators, benchmarks, or evidence binaries during ordinary validation.

The initial validator checks:

- required role presence and uniqueness;
- forbidden generator permissions;
- partition overlap and holdout contamination;
- candidate identity uniqueness, parent existence, and lineage cycles;
- selected-candidate existence and disposition;
- required FAIL and UNKNOWN handling;
- D2 reproducibility and evaluator-corpus requirements;
- D3 protected holdout, predeclared selection, authority separation, executable separation, reviewer binding, and independent evidence;
- MNCS candidate, contract, and environment binding;
- D4 rollback and regeneration-drill results.

The aggregate schema is the minimum interoperable unit for 0.1. Future implementations MAY split it into content-addressed records if they expose an equivalent offline-resolvable aggregate view.

A later RFC may define MNCDS attestation predicates after at least one independent implementation exists.

## Security, privacy, and vendor-neutrality impact

MNCDS reduces risks from evaluator tampering, hidden objective drift, benchmark contamination, selective reporting, unreproducible generation, and unsafe deployment.

It does not eliminate risks from compromised tools, dishonest operators, weak contracts, inadequate threat models, leaked holdouts, colluding evaluators, or undeclared external access.

Sensitive prompts, proprietary datasets, model weights, and private source code MAY remain undisclosed, but a conformance claim MUST still expose stable identities, role bindings, declared access boundaries, evaluation methods, and sufficient evidence for the claimed profile. Redaction MUST NOT be treated as verification merely because disclosure is restricted.

Privacy-preserving proofs, confidential-computing attestations, commitments, and transparency logs MAY be used as namespaced experimental extensions. They do not replace required evidence until a future RFC defines predicate, trust, failure, expiration, revocation, and interoperability semantics.

No model, agent framework, analyzer, compiler, graph system, proof assistant, or orchestration platform is normative. Joern remains one optional structural-analysis provider.

## Compatibility and migration

MNCDS is additive. Existing MNCS 0.1 and 0.2 bundles remain valid under their original rules and do not acquire an MNCDS claim retroactively.

Projects adopting MNCDS MAY wrap an existing development history by identifying the oldest reliably reproducible baseline and marking earlier lineage as UNKNOWN or unavailable. They MUST NOT fabricate missing records or claim protected-holdout separation when none existed.

MNCDS remains separately versioned throughout the MNCS 0.x series. Any future merger into MNCS requires a major-version RFC and explicit migration rules.

## Alternatives

### Put all development rules directly into MNCS

Rejected for this draft because acceptance evidence and development-process governance are related but separable concerns. Combining them would make the core standard harder to adopt and could invalidate otherwise sound historical bundles.

### Publish only non-normative guidance

Rejected because benchmark contamination, objective drift, and unverifiable candidate selection directly affect the credibility of conformance claims.

### Require complete disclosure of prompts, models, datasets, and source

Rejected because it would prevent legitimate proprietary or sensitive use. Stable identities, bounded disclosure, independent evidence, and explicit UNKNOWN are more tool-neutral.

### Require a human to approve every generated change

Rejected because the purpose of MNCS is to permit machine-owned internal complexity under stronger external controls. Human line-by-line review is neither sufficient nor always feasible.

### Forbid recursive improvement

Rejected because evidence-driven improvement of generators and verification harnesses is a central benefit. The standard instead requires versioned epochs, new identities, regression testing, and holdout discipline.

## Test and evidence plan

The repository now contains an executable evidence baseline:

1. **D1 multiple-candidate ledger:** implemented through the D4 reference record reduced to D1 in unit tests.
2. **Reject evaluator or threshold mutation:** implemented in unit tests and deterministic corpus cases.
3. **Reject UNKNOWN promotion:** implemented in unit tests and corpus.
4. **D2 reproducible generation and repeated measurement:** implemented with seeded reproducibility and repeated-measurement checks.
5. **D3 protected holdout and independent evaluator:** implemented in the cumulative reference record and tests.
6. **Recursive harness improvement:** completed by the frozen two-epoch analyzer study
   with retained disagreements, fresh developer-withheld final inputs, resource
   measurements, and an explicit non-promotion boundary.
7. **D4 rollback, regeneration, monitoring, and retirement:** implemented in the reference record and rejection tests.
8. **Independent validator agreement:** the independent Rust consumer reads the
   combined release-candidate corpus directly and agrees with Python on every vector.

Relevant artifacts include:

- `examples/mncds-d4/development-record.json`;
- `tests/test_mncds.py`;
- `mncds-conformance-corpus/corpus.json`;
- `scripts/run-mncds-corpus`;
- `docs/mncds-evidence-plan.md`.

The corpus includes forbidden generator authority, lineage cycles, UNKNOWN promotion, holdout contamination, post-hoc selection, evaluator conflicts, mismatched MNCS binding, untested rollback, and failed regeneration drills.

Before acceptance, an independent consumer MUST process the corpus without importing the Python validator and publish normalized agreement, disagreement, and unsupported-rule outcomes.

## Resolved design questions

The initial 0.1-draft implementation resolves the prior questions as follows:

- MNCDS remains a permanent companion throughout MNCS 0.x; merger may be reconsidered only at a future major version.
- D1 uses one aggregate record containing charter, roles, generator boundary, partitions, evaluators, candidate ledger, selection, and reproducibility declaration.
- Stochastic generation uses `EXACT`, `SEEDED`, `STATISTICAL`, `DISTRIBUTIONAL`, or `NONE`; D2 and above reject `NONE`.
- Baseline D3 independence requires different generator/evaluator authority and executable identities, immutable evaluator configuration, protected evidence, reviewer binding, and selected-candidate results.
- Every materially evaluated candidate is retained individually; pre-material candidates may be summarized only under a predeclared auditable aggregation rule.
- Privacy proofs and transparency logs remain optional namespaced extensions until an interoperability RFC exists.
- MNCS and MNCDS validation remain separate results and commands; a future summary may display both without collapsing them.

Detailed semantics are in `spec/MNCDS-v0.1-records-and-decisions.md`.

## Deferred non-core research questions

- What optional aggregate commitments best preserve million-candidate search history
  while protecting proprietary candidate bodies?
- Which privacy-preserving proof systems are practical for restricted prompts,
  datasets, and model configurations?
- What externally evidenced threshold should define a future higher-assurance
  organizational-independence profile?

## Acceptance gate

RFC 0004 MUST remain Draft until:

- CI passes for schema, validator, tests, example, corpus, package, and documentation;
- an independent corpus consumer publishes normalized agreement;
- a reproducible two-epoch recursive harness study is complete;
- security and privacy review identifies no unresolved claim-broadening issue;
- the independent approvals required by governance are recorded.

## Release-candidate decision record

The repository's 0.1-rc.1 implementation resolves the internally decidable questions
in `spec/MNCS-v0.3-MNCDS-v0.1-decisions.md` and provides a self-contained proposed
specification in `spec/MNCDS-v0.1-rc.1.md`. The aggregate record remains the portable
interoperability unit. Draft records remain valid as draft artifacts and are not
upgraded by changing a version string.

This implementation work does not change this RFC's Draft status. Implementation
agreement, a recursive study, internal review, and local readiness cannot supply the
required non-conflicted approvals or organizational independence.
