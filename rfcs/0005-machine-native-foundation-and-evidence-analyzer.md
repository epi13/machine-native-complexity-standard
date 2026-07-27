# RFC 0005: Machine-Native Foundation and Evidence Analyzer Architecture

- Status: Draft
- Authors: Alexander Collamore
- Created: 2026-07-26
- Review deadline: 2026-08-09
- Target version: MNCS 0.3 (proposed)
- Conflicts disclosed: Repository owner, proposal author, and initial implementation author are the same person; independent review is required before acceptance.

## Summary

This RFC proposes the conceptual and machine-readable foundation surrounding MNCS and
MNCDS and introduces an experimental reference architecture for a focused Machine-Native
Evidence Analyzer (MNEA).

MNCS continues to evaluate implementation evidence. MNCDS continues to evaluate the
process that creates, evaluates, selects, releases, regenerates, and retires an
implementation. This RFC does not merge those conformance families and does not create a
third conformance score.

The proposal adds:

1. a core model for machine-native complexity and its control planes;
2. an experimental contract-adequacy profile;
3. applicability and criticality guidance;
4. component-composition and claim-dependency semantics;
5. an experimental combined assurance-case record that preserves separate MNCS and MNCDS
   results;
6. generic threat-model and measurement frameworks;
7. governance completion criteria; and
8. a bounded, compiler-backed analyzer architecture with explicit PASS, FAIL, and UNKNOWN.

Joern remains useful as historical evidence and as an epoch-one baseline, but it is not a
required dependency. The normative requirement is a reproducible two-epoch analyzer or
harness improvement study, not continued use of one product.

## Motivation

MNCS 0.2 establishes evidence-derived implementation conformance. MNCDS 0.1-draft
establishes development-process controls. Together they answer two central questions:

- What evidence supports accepting this candidate?
- What controls governed the process that produced and selected it?

They do not yet fully standardize several surrounding questions:

- What exactly distinguishes machine-native complexity from ordinary generated code?
- When is the trade justified?
- What makes a readable contract sufficiently testable and non-vacuous?
- How do component claims compose into a system claim?
- How should separate MNCS and MNCDS results be presented together without collapsing
  them?
- What common threat and measurement fields should domain profiles extend?
- What analyzer architecture best produces bounded evidence without turning a particular
  tool into a normative dependency?

The preliminary GraphFlow study also showed that persistent Joern-visible feedback did
not improve the tested optimization outcome and increased elapsed time and token use.
That result supports treating structural analysis as bounded evidence, rejection, and
repair feedback rather than assuming that a general-purpose graph system is inherently
useful optimization guidance.

## Normative proposal

This RFC is Draft. The documents and schemas introduced with it are experimental until an
RFC is accepted under project governance. Existing MNCS 0.2 and MNCDS 0.1-draft claims do
not acquire new requirements retroactively.

### Core model

Machine-native complexity is implementation complexity intentionally permitted to exceed
ordinary human-maintainability limits because it purchases a predeclared, measurable,
operationally useful benefit while remaining inside readable, auditable, bounded, and
reversible control surfaces.

The following distinctions are required:

- **Generated implementation:** implementation produced in whole or part by a machine.
  Generation alone does not make it machine-native.
- **Machine-optimized implementation:** implementation transformed or selected by a
  machine against an objective. It may remain normally human-maintainable.
- **Machine-owned implementation complexity:** internal structure expected to be managed
  primarily through regeneration, evidence, and replacement rather than routine manual
  editing.
- **Machine-native implementation:** an implementation for which machine-owned complexity
  is intentional and governed by readable contracts, evidence, lifecycle controls, and
  rollback or replacement.

The project preserves five distinct planes:

1. **Human control plane:** intended use, readable contract, exclusions, authority,
   acceptance policy, criticality, and risk decisions.
2. **Machine execution plane:** candidate and released artifacts, dependencies, state,
   and runtime behavior.
3. **Evidence plane:** observations, witnesses, counterexamples, measurements,
   attestations, limitations, and explicit UNKNOWN.
4. **Development-control plane:** charter, baseline, generator boundary, partitions,
   evaluator identities, candidate ledger, selection, and epoch history.
5. **Operational-control plane:** release binding, monitoring, rollback, regeneration,
   replacement, revalidation, and retirement.

Human readability is relocated, not eliminated. Complexity is never a useful benefit by
itself.

The following are outside the concept:

- ordinary generated code that remains normally maintainable;
- obfuscation without operational benefit;
- unverifiable output with no readable replacement control system;
- complexity introduced only for novelty, score maximization, or model preference;
- claims with no bounded contract, environment, evidence policy, or lifecycle path; and
- artifacts that cannot be evaluated, contained, replaced, rolled back, or retired at
  the assurance level required by their intended use.

### Contract adequacy

A contract identity does not prove contract adequacy. Strong machine-native claims need a
separately identified contract profile covering at least:

- intended use and exclusions;
- inputs, outputs, state, and state transitions;
- externally observable behavior;
- error, malformed-input, and adversarial-input behavior;
- safety and security invariants;
- resource and timing limits where relevant;
- environment assumptions and external effects;
- compatibility obligations;
- undefined and implementation-defined behavior;
- intentionally excluded behavior;
- reference-oracle limits and measurement tolerances;
- known ambiguities; and
- version and material-change rules.

The experimental `mncs-contract-profile` schema records these fields and an independent
PASS, FAIL, or UNKNOWN result. It does not claim philosophical completeness.

A contract MUST NOT pass an adequacy profile when correctness is circularly defined as
whatever the candidate does. Missing behavior required for the intended evaluation MUST
NOT pass. Material ambiguity SHOULD produce UNKNOWN unless evidence demonstrates a direct
violation, in which case it produces FAIL. A material contract change receives a new
identity and triggers evidence-impact review.

### Applicability and criticality

Machine-native complexity is justified only when the declared benefit exceeds its added
assurance, operational, replacement, and residual-risk costs.

A criticality decision should identify:

- intended use and reasonably foreseeable misuse;
- consequence severity;
- exposure and reversibility;
- data, security, safety, legal, and availability impact;
- required independence;
- tolerated UNKNOWN;
- evidence freshness and revalidation triggers; and
- minimum MNCS and MNCDS expectations under the applicable organizational or domain
  policy.

This RFC does not freeze a universal mapping from `low`, `moderate`, `high`, and
`critical` to MNCS levels or MNCDS profiles. Such a mapping requires adoption evidence
and domain review. A policy that supplies a mapping must be separately identified.

The simpler-alternative rule is:

> When a materially simpler implementation satisfies the same contract, constraints,
> useful-benefit threshold, and assurance requirements, added machine-owned complexity
> should not be preferred without a recorded operational justification.

### Composition and dependency semantics

A component PASS does not automatically imply a system PASS.

A system assurance case should use an explicit claim-dependency graph recording:

- component, runtime, build, service, data, evaluator, and evidence dependencies;
- required and optional relationships;
- interface and environment compatibility;
- shared evidence and correlated failure groups;
- claim versions, freshness, and invalidation triggers;
- mixed MNCS levels and MNCDS profiles; and
- residual risks at system boundaries.

System policy determines aggregation, but it must preserve every required FAIL or UNKNOWN
and must not hide a weaker component result behind an aggregate PASS. Replacement of one
component invalidates only claims whose declared dependency paths or environment bindings
are affected, unless policy states a broader invalidation rule.

### Combined assurance case

The experimental `mncs-assurance-case` schema binds implementation, development, contract,
criticality, trust, dependencies, authorities, limitations, deviations, freshness,
rollback, replacement, and supersession information.

It preserves separate MNCS and MNCDS objects with their own:

- versions;
- claimed levels or profiles;
- statuses;
- result identities;
- issue sets;
- scopes; and
- limitations.

A display may render `MNCDS-D3 / MNCS-L4`, but the record MUST NOT reduce the two results
to a single conformance boolean. An operational `disposition` such as `accepted`,
`rejected`, or `review_required` is a policy decision, not a third conformance result.

### Threat-model framework

A machine-native threat record should identify at least:

- threat identity and category;
- affected plane and assets;
- actor or failure source;
- preconditions and attack or failure path;
- assumptions;
- mitigations and their evidence identities;
- detection and monitoring signals;
- residual risk;
- owner; and
- revalidation triggers.

The baseline taxonomy includes generator authority escape, unauthorized contract or
baseline change, evaluator or threshold manipulation, holdout leakage, benchmark
contamination, selective reporting, evaluator gaming, UNKNOWN promotion, artifact or
model substitution, compromised build or dependencies, false independence, adversarial
runtime inputs, denial of service, resource exhaustion, environment drift, monitoring
failure, rollback failure, regeneration failure, and untracked external access.

Identifying a threat does not prove it is mitigated.

### Measurement framework

A measurement profile should identify:

- legitimate baseline and candidate identities;
- metric, unit, direction, and operational relevance;
- environment, hardware, software, evaluator, and benchmark identities;
- warmup, sample count, repetitions, ordering, and randomization;
- summary statistics, uncertainty, noise, and outlier policy;
- hard constraints and worst-case regression limits;
- multiple-objective and Pareto treatment;
- normalization and comparability rules;
- contamination controls;
- predeclared useful-benefit threshold; and
- evidence freshness.

A process MUST NOT select the best observed run and report it as a repeated-measurement
result. Complexity, novelty, code size, or model preference does not count as a useful
benefit without a documented operational reason.

### Governance completion

Bootstrap governance remains truthful until the project has adopted:

- an explicit maintainer and editor roster;
- succession and inactivity rules;
- release and signing authority;
- an independent reviewer pool or a disclosed inability to form one;
- namespace and mark stewardship without technical veto power;
- conflict and recusal records; and
- a rule that reference validators and analyzers remain non-normative implementations.

This RFC proposes those completion criteria but does not claim they are already satisfied.

### Machine-Native Evidence Analyzer architecture

MNEA is an experimental reference architecture, not a required product. Its purpose is to
evaluate declared structural, behavioral, safety, resource, and implementation
invariants and emit bounded, reproducible PASS, FAIL, or UNKNOWN evidence.

The minimum architecture is:

```text
source or artifact
    -> compiler-backed extractor
    -> normalized evidence facts or graph
    -> declarative invariant evaluator
    -> optional runtime and differential providers
    -> evidence reconciler
    -> MNCS-compatible evidence result
```

The initial experimental provider targets bounded single-file C11 analysis through Clang
AST JSON. It is intentionally narrow and supports only a small invariant set. Unsupported
constructs and unresolved semantics remain UNKNOWN.

The analyzer has two modes:

- **Evaluator mode:** frozen artifact, contract, invariants, policy, bounds, and immutable
  result; no candidate or threshold modification; no protected-holdout disclosure.
- **Repair-feedback mode:** development evidence and compact diagnostics only; no final
  conformance authority and no protected-holdout access.

The same executable may support both modes only when configuration, authority, evidence
partition, and execution identities distinguish them.

No analyzer is a truth oracle. Required provider disagreement is preserved. FAIL dominates
UNKNOWN, which dominates PASS. A behavioral PASS does not broaden into a structural PASS,
and an unsupported structural method does not pass because runtime tests succeeded.

The experimental `mncs-analyzer-result` schema records bounded method, identities,
assumptions, facts, unsupported constructs, witnesses, counterexamples, resources,
limitations, and evidence identity. PASS requires the analyzer to declare required
semantics complete within its bounded method. FAIL requires a witness or counterexample.
UNKNOWN requires an explicit limitation or unsupported construct.

## Schema and validator changes

This RFC introduces three experimental schemas:

- `schemas/mncs-contract-profile.schema.json`;
- `schemas/mncs-assurance-case.schema.json`; and
- `schemas/mncs-analyzer-result.schema.json`.

They are packaged for discovery through `mncs schema` but are not inputs to MNCS 0.2
certification and do not alter existing conformance computation.

The experimental Clang provider uses Provider Protocol 0.1. Ordinary validation remains
offline and never launches the provider, candidate, compiler, or evidence binary.

## Security, privacy, and vendor-neutrality impact

The proposal reduces claim broadening by separating contract adequacy, implementation
conformance, development control, composition, trust, and operational disposition. It
also gives unsupported analyzer semantics an explicit UNKNOWN path.

The Clang provider executes only through the explicit provider command. It invokes Clang
without a shell, caps source size and wall time, and does not claim filesystem or network
isolation. The provider and compiler remain untrusted inputs to the final assurance case.

No compiler, analyzer, graph system, model, agent framework, or vendor is normative. Joern,
Clang, LLVM, symbolic execution, model checking, runtime instrumentation, custom tools,
and independent combinations may all produce evidence under declared bounds.

Sensitive contracts, prompts, datasets, models, or source may remain restricted, but
redaction does not create verification. Required hidden material remains UNKNOWN unless
an accepted independent attestation or privacy-preserving predicate establishes the
necessary fact.

## Compatibility and migration

The proposal is additive and experimental.

Existing MNCS 0.1, 0.1.1, and 0.2 artifacts remain governed by their original rules.
Existing MNCDS records remain governed by MNCDS 0.1-draft. Projects may add experimental
contract profiles or assurance cases without changing historical conformance results.

A future accepted version must define migration and whether any profile becomes required
for newly issued claims. Historical claims must not be rewritten retroactively.

## Alternatives

### Keep Joern as the required recursive-study tool

Rejected. The standard needs evidence that controlled recursive improvement works, not
continued dependence on a tool whose tested agent-visible feedback did not improve the
observed outcome.

### Build another universal Code Property Graph platform

Rejected. A universal graph platform is much larger than the evidence problem and would
make the reference implementation difficult to validate and replace.

### Add contract fields directly to the MNCS manifest

Deferred. Contract adequacy is separable from implementation conformance and needs
experimental evidence before becoming a mandatory MNCS field.

### Collapse MNCS and MNCDS into one assurance score

Rejected. The two claims evaluate different facts. Collapsing them would conceal whether
a failure arose from implementation evidence or development-process control.

### Leave composition entirely to adopters

Rejected as a foundation. Domain policies may choose aggregation rules, but the standard
still needs a portable way to identify dependencies, correlated failures, and preserved
FAIL or UNKNOWN results.

## Test and evidence plan

Before this RFC can be accepted:

1. all three schemas must self-validate under JSON Schema Draft 2020-12;
2. positive and negative fixtures must test status, identity, and non-collapse semantics;
3. at least one independent implementation must consume each schema used normatively;
4. the Clang provider corpus must contain valid, violating, unsupported, crash, timeout,
   aliasing, indirect-call, macro, mutation, and naive-false-PASS cases;
5. analyzer comparisons must report true positives, false positives, false negatives,
   incorrect PASS, UNKNOWN, crashes, timeouts, runtime, memory, determinism, and diagnostic
   utility;
6. the epoch-one Joern baseline must be frozen and identified;
7. an epoch-two analyzer or harness must receive new identities and use a fresh protected
   holdout;
8. disagreements must become regression fixtures or remain UNKNOWN;
9. the study must produce an MNCDS record and an MNCS bundle for any selected candidate;
10. security and privacy review must find no unresolved claim-broadening defect; and
11. governance-required independent approvals must be recorded.

## Unresolved questions

- Which contract fields should become mandatory in a future MNCS version?
- Which criticality-to-assurance mappings have enough evidence for a normative profile?
- How should correlated dependency failures be normalized across implementations?
- What evidence freshness defaults are reasonable across domains?
- Which C semantics can the first analyzer soundly classify rather than preserve as
  UNKNOWN?
- What independent implementation should consume the new schemas?
- What evidence threshold should distinguish baseline evaluator independence from a future
  higher-assurance profile?
- How should proprietary million-candidate histories be committed without disclosing
  candidate bodies?
