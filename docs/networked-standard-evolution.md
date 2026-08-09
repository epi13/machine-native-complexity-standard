# Networked Standard Evolution

## Purpose

MNCS is intended to improve through evidence produced across a network of standards,
representations, language experiments, verification tools, recursive mechanisms,
independent implementations, and human governance. No single repository component is
the standard, the evaluator, and the promotion authority at the same time.

This document describes a non-normative architecture for progressing MNCS and MNCDS.
It does not change conformance semantics, approve an RFC, promote an implementation, or
replace the governance and release processes.

The central distinction is between two related but separate loops:

1. **implementation refinement** improves a bounded candidate under an existing version
   of the standard; and
2. **standard evolution** changes the rules, identities, representations, or assurance
   semantics used by future candidates.

Evidence may flow from the first loop into the second. Success in the first loop does
not automatically authorize a change to the standard.

## Component roles

| Component | Primary role | Produces | Must not do |
|---|---|---|---|
| **MNCS** | Define versioned acceptance semantics, claim boundaries, identities, invariants, evidence relationships, comparison rules, and conformance outcomes | Specifications, schemas, canonical identities, conformance rules, compatibility requirements, and reference vectors | Depend normatively on one language, compiler, agent, analyzer, provider, or orchestration system |
| **MNCDS** | Define the governed development process around candidate generation, evidence eligibility, lineage, evaluation partitions, selection, freeze, replacement, rollback, and retirement | Development records, candidate lineage, authority boundaries, feedback-eligibility records, selection records, lifecycle records, and regeneration obligations | Convert development success into MNCS conformance or allow selection evidence to become unrestricted repair feedback |
| **MNCS Language** | Explore how contracts, effects, capabilities, assumptions, evidence, diagnostics, compiler transformations, and repair structures can be represented directly in a general-purpose language | Experimental source forms, canonical semantic graphs, high-level and verified IR, diagnostics, semantic patches, transformation histories, and compiler evidence | Redefine MNCS meaning through syntax, hide authority in compiler behavior, or certify its own compiler solely through self-hosting |
| **MNCS Forge** | Run bounded provider-neutral development workflows, micro-verifiers, causal localization, candidate checks, and evidence production | Verifier records, diagnostic obligations, causal slices, semantic and evidence deltas, provider identities, workflow records, and candidate evaluation inputs | Become a normative dependency, invent missing evidence, silently substitute source inspection for unavailable analysis, or promote a candidate |
| **RAVEL** | Coordinate recursive and distributed experimentation across agents, machines, implementations, verifiers, environments, and trust boundaries | Distributed execution records, experiment lineage, bounded adaptation proposals, cross-host comparisons, retained failures, and orchestration evidence | Rewrite the evaluator, thresholds, partitions, resource ceilings, custody, or release authority |
| **Promotion policy and governance** | Decide whether evidence is sufficient to trust, select, release, standardize, deprecate, or reject a candidate or proposal | Promotion decisions, RFC dispositions, release authorization, signed releases, migration requirements, minority views, and retained blockers | Treat tool output as self-executing authority or permit an author, generator, or implementation to approve its own contested normative change |
| **Independent evaluators, implementations, custodians, and witnesses** | Supply diversity, external checks, protected material, custody, reproduction, and disagreement evidence | Independent implementation reports, externally held evaluation results, attestations, custody records, and counterexamples | Be inferred from running the same implementation under a different label or on another machine controlled by the same authority |

The boundaries are intentional. Components may exchange machine-readable artifacts, but
an artifact does not inherit the authority of the component that consumes it.

## Network model

The project family can be understood as an evidence and proposal network:

```text
MNCS / MNCDS
  define standards, identities, invariants,
  deterministic representations, development controls,
  and comparison rules
        |
        v
MNCS Language and other implementations
  expose semantics, compiler transformations,
  diagnostics, evidence, and repair structures
        |
        v
Forge and replaceable providers
  run micro-verifiers, localize failures,
  test candidate changes, and produce evidence
        |
        v
RAVEL and other orchestration mechanisms
  distribute experiments across agents, machines,
  implementations, environments, and trust boundaries
        |
        v
Independent evaluation and custody
  challenge results, preserve held-out material,
  reproduce claims, and expose disagreement
        |
        v
Promotion policy and governance
  accept, reject, defer, standardize, release,
  deprecate, or retain UNKNOWN
        |
        +---- versioned decisions and new questions ----+
                                                        |
                                                        v
                                            next bounded research cycle
```

This is a network, not a hierarchy in which the most automated component owns the
others. The standard constrains evidence interpretation. Implementations expose
observable structure. Forge and providers answer bounded questions. RAVEL coordinates
work. Independent actors challenge the result. Governance controls normative and
release authority.

## Implementation-refinement loop

An implementation-refinement loop operates under a fixed standard version, evaluator,
policy, and resource boundary:

```text
observe candidate and evidence state
  -> localize a failed, weak, stale, or conflicting obligation
  -> propose an isolated descendant candidate
  -> declare intended improvements and protected properties
  -> run bounded verifiers and evaluators
  -> compare semantic, authority, complexity, performance, and evidence deltas
  -> accept, reject, or retain UNKNOWN under explicit policy
  -> record lineage, cost, rollback, and retained failures
```

The loop may improve source syntax, compiler passes, lowering strategies, verifier
interfaces, routing policies, repair strategies, or other implementation surfaces. It
must not silently change the standard version or evaluator used to judge the candidate.

MNCDS records how feedback was used and which evidence remained unavailable to the
generator. MNCS evaluates the frozen candidate's declared claim. Forge and RAVEL may
support the loop, but neither supplies promotion authority merely by operating it.

## Standard-evolution loop

A standard-evolution loop begins when repeated evidence suggests that existing
semantics, representations, or rules are incomplete, ambiguous, unnecessarily costly,
or unable to distinguish important outcomes.

```text
cross-implementation observations and counterexamples
  -> bounded problem statement
  -> competing change proposals
  -> explicit compatibility and authority analysis
  -> experimental schemas, profiles, or representations
  -> multiple implementations and adversarial fixtures
  -> independent comparison and disagreement record
  -> RFC review under governance
  -> accept, reject, revise, or defer
  -> versioned release and migration material
```

The standard should learn from the network, but it should not be directly rewritten by
it. Machine-generated RFC text, schemas, fixtures, or migration proposals remain
proposals until the governance process accepts them.

A successful implementation experiment may establish that a proposal is useful within
a declared scope. It does not establish that the proposal is universally applicable,
compatible, secure, independently implemented, or ready to become normative.

## Evidence flowing into standard evolution

Useful evidence for changing the standard may include:

- recurrent ambiguity observed across more than one implementation;
- equivalent semantic claims represented with materially different verifier cost;
- incompatibilities exposed by independent consumers;
- counterexamples that the current schema cannot represent honestly;
- repeated authority, freshness, composition, or invalidation failures;
- differences between compiler backends or language profiles that affect claim meaning;
- micro-verifier results showing that a required distinction is currently hidden;
- RAVEL experiments showing that one development policy transfers better than controls;
- failed or `UNKNOWN` cases retained across candidate generations;
- migration experiments demonstrating whether an additive change is actually compatible;
- security, privacy, custody, or organizational-independence findings; and
- evidence that a proposed simplification preserves all declared meaning rather than
  merely shortening the representation.

Evidence should preserve subject identity, producer identity, method, environment,
assumptions, limitations, and eligibility. Aggregation must not erase disagreement or
turn several dependent observations into apparent independence.

## Separate identities and versions

The following surfaces should remain independently identifiable and versioned where
applicable:

- MNCS specification and schema version;
- MNCDS specification and development-record version;
- canonical semantic representation version;
- human source-language grammar and formatter version;
- compiler implementation and pass identities;
- high-level and verified IR versions;
- backend and lowering-policy identities;
- Forge version, configuration, workflow, and provider identities;
- verifier and evaluator implementation identities;
- RAVEL mechanism, orchestration policy, environment, and experiment identities;
- promotion policy and trust-profile identities; and
- RFC, governance decision, release artifact, and migration identities.

Independent versioning prevents synchronized co-evolution from masquerading as
verification. If a syntax, compiler, verifier, evaluator, and acceptance rule all change
together, their agreement may only show that the components were changed to agree.
Compatibility and evidence must be evaluated across fixed boundaries and, where
possible, diverse implementations.

## Interfaces between components

The network should exchange bounded artifacts rather than unrestricted hidden state.
Representative interfaces include:

| Producer | Consumer | Artifact |
|---|---|---|
| MNCS / MNCDS | Implementations and validators | Versioned specifications, schemas, canonicalization rules, conformance corpus, and development profiles |
| MNCS Language | Forge, compilers, and evaluators | Semantic graph projections, diagnostics, IR, evidence claims, transformation records, and semantic patches |
| Forge providers | MNCDS records and candidate evaluators | Identity-bearing verifier results, causal slices, capability declarations, and bounded failure reasons |
| RAVEL | Evaluators, MNCDS, and research studies | Experiment plans, distributed execution records, candidate lineage, environment identities, budgets, and retained outcomes |
| Independent actors | Governance and release preparation | Implementation reports, reproduction records, custody attestations, counterexamples, and disagreement findings |
| Governance | The project network | RFC decisions, accepted semantics, explicit blockers, release authorization, deprecations, and migration requirements |

Private chain-of-thought is not a required interface. Compact claims, observations,
identities, predictions, alternatives, falsifiers, and witnesses are sufficient and more
auditable.

## Promotion is an authority boundary

Promotion policy is not merely another optimizer in the recursive network. It is the
explicit authority boundary that decides whether a candidate or proposal may become:

- the selected implementation for a declared study;
- a frozen candidate eligible for final evaluation;
- an accepted experimental profile;
- normative specification text or schema;
- a release candidate;
- a signed release;
- a deprecated representation or behavior; or
- a rejected or retained-`UNKNOWN` result.

Different promotion surfaces require different evidence. Passing a development check
may select a candidate for more testing but cannot authorize a release. Passing an MNCS
claim under one environment cannot approve an RFC. A merged research document cannot
establish independent evaluation. A signed release cannot retroactively make weak
supporting evidence independent.

Promotion decisions should bind at least:

- the exact candidate or proposal identity;
- the governing standard, policy, and evaluator identities;
- evidence considered and evidence explicitly excluded;
- unresolved `UNKNOWN`s, dissent, and conflicts;
- the authority making the decision;
- compatibility and migration consequences;
- rollback or supersession behavior; and
- the scope beyond which the decision must not be reused.

## Minimum progression discipline

A network-derived proposal to change normative meaning should ordinarily provide:

1. a precise problem or counterexample under the current version;
2. the affected identities, invariants, claims, or assurance semantics;
3. at least one competing alternative or a reason alternatives are infeasible;
4. explicit authority, security, privacy, and compatibility analysis;
5. valid, invalid, ambiguous, and adversarial fixtures;
6. implementation evidence from more than the proposing tool when feasible;
7. migration and versioning behavior;
8. retained failures, disagreements, and `UNKNOWN`s;
9. a statement of what the evidence cannot establish; and
10. RFC review and approval required by governance.

A tool-specific feature may remain an experimental extension without satisfying all
requirements for normative inclusion. Experimental success should be preserved as
useful evidence rather than overstated as standard adoption.

## Failure modes to prevent

### Tool capture

A reference validator, Forge provider, compiler, language, or RAVEL mechanism becomes
normative in practice because all examples depend on it. The remedy is public schemas,
portable fixtures, replaceable providers, independent consumers, and explicit
non-normative implementation status.

### Self-certification

A generator proposes a change, runs its own evaluator, controls the evidence partition,
and promotes the result. The remedy is separated authority, immutable evaluation,
feedback eligibility, external custody where required, and independent review.

### Synchronized agreement

The representation, implementation, verifier, and acceptance rule change together and
then agree. The remedy is independently versioned surfaces, frozen comparison points,
cross-version tests, and diverse implementations.

### Evidence laundering

Local, same-family, operator-controlled, or development evidence is aggregated until it
appears independent or final. The remedy is preserved provenance, evidence classes,
non-additive independence claims, and explicit `UNKNOWN` outcomes.

### Benchmark constitutionalism

A benchmark or study becomes the de facto definition of correctness. The remedy is a
versioned semantic specification, multiple task families, adversarial fixtures, transfer
tests, and a claim boundary narrower than the benchmark result.

### Recursive authority expansion

A recursive mechanism improves its score by changing thresholds, evaluator code,
resource ceilings, partitions, or promotion rules. The remedy is a governor outside the
candidate's mutation authority and fail-closed identity checks.

### Governance automation by accident

A passing workflow automatically merges normative text or creates a release. Automation
may prepare evidence and verify prerequisites, but final normative and release decisions
remain governed acts with recorded authority.

## Practical progression sequence

The project family should generally progress a new idea through the following sequence:

1. **Observe** — retain a bounded failure, ambiguity, cost, disagreement, or opportunity.
2. **Localize** — identify the smallest semantic, implementation, verifier, or policy
   surface implicated by the evidence.
3. **Propose** — create competing isolated changes with predicted effects and protected
   properties.
4. **Experiment** — use Forge, RAVEL, language prototypes, providers, and independent
   implementations under declared budgets and partitions.
5. **Compare** — preserve semantic, authority, performance, complexity, evidence, and
   compatibility deltas, including failures and `UNKNOWN`s.
6. **Generalize cautiously** — test transfer and identify the exact scope in which the
   lesson holds.
7. **Standardize through RFC** — propose normative meaning only when the evidence and
   compatibility case justify it.
8. **Authorize and release** — follow governance, release, signing, migration, and
   deprecation requirements.
9. **Continue observation** — treat the release as a new fixed boundary for subsequent
   bounded research rather than as proof that evolution is complete.

## Claim boundary

This networked architecture can make standard evolution more empirical, distributed,
auditable, and resistant to single-tool capture. It can help the project discover better
representations, development controls, verifier interfaces, language structures, and
assurance semantics.

It cannot make normative judgment disappear, convert recursion into independence,
create protected custody from operator-controlled machines, prove general recursive
self-improvement, or allow the project family to certify itself. Missing authority or
independent evidence remains `UNKNOWN`.