# RFC 0004: Machine-Native Complexity Development Specification

- Status: Draft
- Authors: Alexander Collamore
- Created: 2026-07-26
- Review deadline: 2026-08-09
- Target version: MNCS 0.3 (proposed)
- Conflicts disclosed: Repository owner and proposal author are the same person; independent review is required before acceptance.

## Summary

This RFC proposes the **Machine-Native Complexity Development Specification (MNCDS)** as a normative companion to MNCS.

MNCS currently defines the evidence and acceptance envelope for machine-native implementations. MNCDS defines the development lifecycle that produces a candidate for that envelope: problem declaration, baseline capture, candidate generation, constrained search, evaluation, selection, independent verification, release, monitoring, regeneration, and retirement.

The central rule is:

> A machine-native implementation may be difficult for humans to maintain internally, but the process that creates, selects, validates, reproduces, and replaces it must remain explicit, bounded, inspectable, and reversible.

MNCDS does not prescribe a particular model, optimizer, programming language, analyzer, search algorithm, or development platform. It standardizes the control surfaces and records needed to distinguish disciplined machine-native development from unbounded code generation or unverifiable optimization.

## Motivation

MNCS 0.2 establishes evidence-derived conformance, reproducible packages, provider interoperability, explicit trust, and scoped certification. Those mechanisms answer whether a submitted implementation is supported by adequate evidence inside a declared contract and environment.

They do not fully answer how the implementation was produced.

A development process can satisfy an output test while still being poorly controlled. Examples include:

- repeatedly tuning against the final acceptance suite until it becomes training data;
- changing the objective after seeing candidate results;
- selecting a candidate without preserving rejected alternatives or the selection rationale;
- accepting an apparent performance gain caused by measurement noise, environmental drift, or a weakened baseline;
- using an analyzer whose failures are silently treated as absence of defects;
- allowing a generator to modify the contract, reference implementation, evaluator, or acceptance threshold it is supposed to satisfy;
- losing the prompts, model identity, seeds, toolchain, datasets, or search history needed to reproduce or replace the candidate;
- deploying a machine-native artifact without a rollback trigger or regeneration path.

A standard for machine-native complexity therefore needs two distinct but connected layers:

1. **MNCS:** what evidence is required to accept a candidate.
2. **MNCDS:** what controls are required while developing and selecting that candidate.

This separation also preserves tool neutrality. MNCDS governs the process and records, not the internal design of a model or optimizer.

## Normative proposal

The proposed normative text is introduced as `spec/MNCDS-v0.1-draft.md`.

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
- separate development evidence from holdout or final acceptance evidence;
- prevent the candidate generator from silently changing the contract, evaluator, reference behavior, or acceptance policy;
- record each materially evaluated candidate and its lineage in an append-only experiment ledger;
- report evaluator and analyzer outcomes as PASS, FAIL, or UNKNOWN without converting missing or unsupported analysis into PASS;
- predeclare the candidate-selection rule before final holdout evaluation;
- preserve rejected candidates or their content identities, measurements, and rejection reasons sufficiently to audit selection pressure;
- require independent verification of the selected candidate against fresh or previously inaccessible evidence;
- produce an MNCS bundle for any conformance claim;
- define rollback, regeneration, monitoring, and retirement conditions before deployment.

### Development conformance profiles

The draft defines cumulative process profiles:

- **MNCDS-D1 — Controlled generation:** charter, baseline, bounded generator authority, candidate identity, and basic ledger.
- **MNCDS-D2 — Reproducible experimentation:** pinned environment, evaluation partitions, repeated measurements, and reproducible candidate lineage.
- **MNCDS-D3 — Independent selection:** predeclared selection policy, protected holdout, independent evaluator, and explicit treatment of UNKNOWN.
- **MNCDS-D4 — Operational regeneration:** release binding, rollback triggers, monitoring, regeneration drills, and retirement records.

These profiles describe development-process assurance and MUST NOT be presented as substitutes for MNCS conformance levels. A project may state both, for example, `MNCDS-D3 / MNCS-L4`, provided each claim is independently supported.

### Separation of authority

The draft distinguishes these roles:

- contract authority;
- generator authority;
- evaluator authority;
- selection authority;
- release authority;
- independent reviewer.

One person or system MAY hold multiple roles in small experiments, but role overlap MUST be disclosed. For D3 and above, the final independent evaluator MUST not be the same executable agent, key identity, or mutable evaluation process used to generate or rank candidates.

### Recursive improvement

MNCDS explicitly permits recursive use of generated evidence to improve a generator, harness, analyzer, or search strategy. This is an important use case, including using results from alternative implementations to improve a Joern-based harness.

Recursive improvement MUST preserve epoch boundaries:

- evidence from development epoch `n` MAY inform the tools and search policy of epoch `n+1`;
- the updated toolchain MUST receive a new identity and version;
- protected holdout evidence from epoch `n` MUST NOT silently become development evidence for the same acceptance claim;
- claims made before the update remain bound to the old toolchain and evidence identities;
- a materially changed harness MUST be revalidated against its own conformance corpus before evaluating new candidates.

This allows the system to learn from its own outputs without erasing provenance or contaminating final evaluation.

## Schema and validator changes

This RFC initially proposes additive, experimental schemas:

- `mncds-development-record.schema.json`
- `mncds-candidate-record.schema.json`
- `mncds-experiment-ledger.schema.json`
- `mncds-selection-record.schema.json`
- `mncds-release-control.schema.json`

The first implementation SHOULD validate documents and cross-document identities offline. It MUST NOT execute generators, candidates, analyzers, or benchmarks during ordinary validation.

The development record should bind:

- specification and contract identities;
- baseline artifact identity;
- development and holdout partition identities;
- generator and toolchain identities;
- candidate lineage;
- objective and constraints;
- selection rule;
- selected candidate;
- independent evaluation results;
- resulting MNCS manifest or package identity;
- rollback and regeneration controls.

A later RFC may define attestation predicates for MNCDS records after at least one independent implementation exists.

## Security, privacy, and vendor-neutrality impact

MNCDS reduces risks from evaluator tampering, hidden objective drift, benchmark contamination, selective reporting, unreproducible generation, and unsafe deployment.

It does not eliminate risks from compromised tools, dishonest operators, weak contracts, inadequate threat models, leaked holdouts, colluding evaluators, or generator access to undeclared external systems.

Sensitive prompts, proprietary datasets, model weights, and private source code MAY remain undisclosed, but a conformance claim MUST still expose stable identities, role bindings, declared access boundaries, evaluation methods, and sufficient evidence for the claimed profile. A redacted field MUST NOT be treated as verified merely because disclosure is restricted.

No vendor-specific model, agent framework, analyzer, compiler, graph system, proof assistant, or orchestration platform is normative. Joern remains one optional structural-analysis provider.

## Compatibility and migration

MNCDS is additive. Existing MNCS 0.1 and 0.2 bundles remain valid under their original rules and do not acquire an MNCDS claim retroactively.

Projects adopting MNCDS MAY wrap an existing development history by identifying the oldest reliably reproducible baseline and clearly marking earlier lineage as UNKNOWN or unavailable. They MUST NOT fabricate missing experiment records or claim protected holdout separation when none existed.

The initial draft uses a separate `MNCDS` version number so process semantics can evolve without implying a breaking change to every MNCS manifest. Accepted releases should publish an explicit compatibility table between MNCDS and MNCS versions.

## Alternatives

### Put all development rules directly into MNCS

Rejected for this draft because acceptance evidence and development-process governance are related but separable concerns. Combining them would make the core standard harder to adopt and could invalidate otherwise sound historical bundles.

### Publish only non-normative guidance

Rejected because benchmark contamination, objective drift, and unverifiable candidate selection directly affect the credibility of conformance claims. Pure guidance would not support an auditable process claim.

### Require complete disclosure of prompts, models, datasets, and source

Rejected because it would prevent legitimate proprietary or sensitive use. Stable identities, bounded disclosure, independent evidence, and explicit UNKNOWN are more tool-neutral.

### Require a human to approve every generated change

Rejected because the purpose of MNCS is to permit machine-owned internal complexity under stronger external controls. Human line-by-line review is neither sufficient nor always feasible.

### Forbid recursive improvement

Rejected because evidence-driven improvement of generators and verification harnesses is a central benefit. The standard instead requires versioned epochs, new identities, and holdout discipline.

## Test and evidence plan

Before acceptance, the proposal should demonstrate at least:

1. A minimal MNCDS-D1 example with multiple generated candidates and a complete ledger.
2. A rejected example where the generator modifies the evaluator or threshold.
3. A rejected example where UNKNOWN analyzer output is omitted or converted to PASS.
4. A D2 example with reproducible candidate generation and repeated performance measurement.
5. A D3 example with a protected holdout and an independent evaluator.
6. A recursive harness-improvement example in which epoch-one evidence improves the epoch-two analysis harness without reusing the protected holdout.
7. A D4 example containing rollback triggers, regeneration instructions, a drill result, and retirement criteria.
8. An independent validator or corpus consumer that agrees on normalized outcomes.

The conformance corpus should include cross-document identity failures, candidate-lineage cycles, undeclared objective changes, missing rejected-candidate records, stale baselines, leaked holdout identifiers, role conflicts, and mismatched MNCS package bindings.

## Unresolved questions

- Should MNCDS remain a permanent companion standard or merge into MNCS at a future major version?
- Which records are mandatory at D1 without making small experiments prohibitively expensive?
- How should the standard represent stochastic generation when exact bitwise regeneration is impossible?
- What minimum evidence demonstrates that an evaluator is sufficiently independent?
- How much rejected-candidate history must be retained when a search evaluates millions of candidates?
- Should privacy-preserving proofs or transparency logs become an optional higher-assurance profile?
- Should a future MNCS certification command report development-process and implementation conformance together or as separate results?
