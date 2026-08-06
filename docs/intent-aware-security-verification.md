# Intent-aware security verification

> Experimental, non-normative design note. This document does not change MNCS or
> MNCDS conformance, promotion, evidence-class, custody, or governance rules.

MNCS is intended to make machine-optimized and less orthodox implementations auditable
through bounded evidence. Security analysis must therefore avoid two opposite errors:

1. treating unfamiliar code as insecure merely because it departs from conventional
   style; and
2. treating intentional or high-performance code as acceptable without evidence that
   its safety properties still hold.

The proposed model is **intent-aware, invariant-driven security verification**. A
suspicious construct is a request for evidence, not an automatic verdict. Declared
intent may explain why a construct exists, but intent never overrides a failed safety
property.

The central principles are:

> **Orthodoxy is a heuristic. Invariants are the authority.**
>
> **Exploitability determines priority; invariant violation determines whether a
> weakness is real.**
>
> **Flag the unusual, verify the semantics, preserve the intent, and reject the
> construct when the evidence fails.**

## Weaknesses do not require a complete exploit chain

A confirmed weakness should normally be repaired even when no coherent attack chain is
currently known. Reachability, deployment, permissions, adjacent components, and attack
techniques can change. A locally contained weakness today can become a useful link in a
future chain.

This does not mean every scanner warning should trigger an automatic rewrite. The
system must distinguish:

- a confirmed violated invariant;
- a suspicious pattern that requires more evidence;
- an intentional deviation whose required invariants are satisfied;
- an unsupported or ambiguous case that remains `UNKNOWN`; and
- a complete or partial attack path that changes urgency and impact.

A finding can therefore state both:

```yaml
weakness_present: true
current_reachability: false
known_attack_chain: none
future_composition_risk: medium
recommended_action: harden
```

A missing attack chain must not be translated into `PASS`. Conversely, an unfamiliar
construct must not be translated into `FAIL` without evidence of a violated property.

## Three verification layers

The micro-verifier network should separate local safety from composition.

### Layer 1: local invariants

Local verifiers check narrow properties such as:

- memory bounds and object lifetime;
- integer range, conversion, and wraparound semantics;
- parsing and validation order;
- path confinement;
- resource ownership and cleanup;
- secret handling;
- concurrency and synchronization assumptions; and
- defined language and compiler behavior.

These verifiers ask whether the component itself can enter a forbidden state.

### Layer 2: boundary invariants

Boundary verifiers check transitions involving authority or trust:

- authentication and resource-specific authorization;
- privilege transitions;
- FFI and process boundaries;
- filesystem and network boundaries;
- deserialization and protocol-state transitions;
- trusted-to-untrusted data movement;
- secret egress; and
- sandbox or capability containment.

These verifiers ask whether data, control, or privilege crosses a boundary under the
required conditions.

### Layer 3: composition and attack paths

Composition verifiers combine bounded findings across components and environments:

- source-to-sink reachability;
- cross-service trust assumptions;
- deployment exposure;
- privilege escalation paths;
- multi-step attack graphs;
- ordering and race-sensitive chains; and
- interactions among individually low-severity weaknesses.

Layer 3 informs urgency and consequence. It must not be the sole authority for deciding
whether Layer 1 or Layer 2 violations are genuine.

## Suspicion routes verification

The proposed workflow is:

```text
unusual or security-relevant construct detected
        |
        v
is there a declared intent and scope?
        |
        v
which invariants must hold for this construct to be acceptable?
        |
        v
run the bounded specialized verifiers
        |
        v
inspect compiler/runtime behavior when required
        |
        v
accept, constrain, reject, repair, or retain UNKNOWN
```

A generic analyzer may identify a computed jump, raw pointer, broad capability,
intentional wraparound, inline assembly block, or validation bypass. That initial signal
should activate the appropriate verification bundle rather than immediately normalize
the implementation into a conventional form.

Without this separation, an agentic repair loop can erase the very implementation
strategies MNCS is intended to study:

```text
unusual implementation
-> generic warning
-> conventional rewrite
-> lost performance or expressiveness
-> false appearance of increased safety
```

## Proof-carrying intentional deviations

An intentional non-orthodox construct should carry a small machine-readable deviation
record. The record is evidence metadata, not a waiver.

```yaml
id: MNCS-DEV-0042
scope:
  artifact: interpreter/dispatch.c
  symbols:
    - execute_bytecode
construct: computed-goto-dispatch
purpose: reduce interpreter dispatch overhead
conventional_concern: indirect control flow
required_invariants:
  - branch targets come only from a closed static table
  - the dispatch index is bounds checked
  - the target table is not writable at runtime
  - untrusted input cannot provide an address
  - control-flow integrity remains within the declared target set
compiler_semantics:
  language: gnu-c11
  compilers:
    - clang-20
    - gcc-16
  optimization:
    - O2
    - O3
target_envelope:
  architectures:
    - x86_64
  operating_systems:
    - linux
required_evidence:
  - control-flow target-set verification
  - optimized IR or assembly inspection
  - sanitizer execution
  - coverage-guided fuzzing
  - benchmark comparison against the reference dispatch loop
known_risks:
  - target-specific extension
  - reduced portability
fallback: portable switch-based dispatcher
revalidate_on:
  - compiler change
  - optimization-profile change
  - target change
  - dispatch-table change
```

The record should bind to exact artifact, compiler, configuration, and environment
identities. A declaration such as `this is intentional` is insufficient by itself.

## Exceptions must be semantic, not syntactic

The network must not learn broad rules such as:

- computed gotos are safe;
- unsigned overflow is allowed;
- raw pointers are acceptable; or
- inline assembly can bypass ordinary checks.

It may accept a specific use only when the required semantic properties hold within a
bounded target envelope.

For example, intentional modulo arithmetic may be valid in a hash or sequence-number
operation and dangerous in an allocation-size calculation. The verifier should reason
about data flow, downstream use, conversion, and bounds rather than whitelist the
syntax.

This prevents an accepted deviation from becoming a permanent scanner blind spot.

## Compiler semantics are part of the security boundary

Less orthodox implementation techniques frequently rely on compiler behavior. MNCS
must distinguish intentional unusual behavior from intentional reliance on undefined or
unstable behavior.

A construct that appears logical in source can be invalid under the language abstract
machine. An optimizer may then remove checks, reorder operations, assume impossible
states, or transform control flow in ways that defeat the programmer's expectation.

An intent-aware verifier bundle may therefore require:

- language-level defined-behavior checks;
- compiler diagnostics and sanitizers;
- source-to-IR or source-to-assembly correspondence checks;
- cross-compiler comparison;
- optimization-level comparison;
- target-specific semantic declarations; and
- differential execution against a simpler reference implementation.

A future MNCS language or compiler layer may define operations that conventional
languages leave ambiguous, such as explicit wrapping arithmetic, saturating arithmetic,
checked pointer formation, or bounded indirect dispatch. Until then, unsupported
compiler assumptions remain `UNKNOWN` or cause rejection within the declared envelope.

## Finding dimensions

A single severity label is too lossy for agentic repair and composition. A finding
should preserve independent dimensions such as:

```yaml
invariant_status: violated
confidence: high
intent_declared: true
attacker_influence: indirect
current_reachability: deployment-dependent
privilege_impact: high
composability: high
repair_cost: low
regression_risk: low
portability_effect: none
recommended_disposition: repair
```

Suggested dimensions include:

- invariant status;
- evidence confidence;
- declared intent and record identity;
- attacker influence;
- current reachability;
- affected trust boundary;
- confidentiality, integrity, availability, and privilege impact;
- composability;
- target and portability limits;
- repair confidence and cost;
- regression and performance risk; and
- revalidation triggers.

This permits decisions such as: not presently reachable, high consequence if exposed,
cheap to repair, therefore fix now.

## Dispositions

The network should avoid reducing every result to an unconditional pass or fail.
Candidate dispositions include:

- `accepted_with_constraints`: intent is declared and all required invariants pass
  inside the bound target envelope;
- `experimental`: local evidence is promising but compiler, portability, composition,
  or operational evidence remains incomplete;
- `repair_required`: a confirmed weakness exists and a bounded repair is available;
- `rejected`: a required invariant fails or the implementation depends on unsupported
  behavior;
- `review_required`: human or governance review is required, without implying an MNCS
  result; and
- `UNKNOWN`: capability, evidence, environment, or authority is insufficient.

These are development workflow dispositions unless and until a future RFC assigns them
normative meaning. They must not be confused with MNCS, MNCDS, evidence-class, or
promotion statuses.

## Agentic repair loop

A security-aware Forge workflow should repair evidence-backed weaknesses without
blindly rewriting every suspicious construct:

1. identify the violated invariant or unresolved suspicion;
2. emit the bounded source, sink, control-flow, state, or compiler evidence;
3. associate any intentional-deviation record;
4. classify confidence, reachability, consequence, and composition potential;
5. propose the smallest structural repair or containment change;
6. apply the change only within the declared candidate scope;
7. run functional and regression checks;
8. rerun the original verifier;
9. run adjacent verifiers for newly introduced boundary or composition failures;
10. compare performance and artifact identity where the original intent was
    performance-related; and
11. preserve the before/after evidence and remaining limitations.

A finding disappears only because the relevant invariant now holds, not because the
agent edited the warning site or suppressed the analyzer.

## Recursive learning without homogenization

The network may learn from accepted deviations, but it must retain the complete verified
pattern:

```text
technique
+ intended purpose
+ compiler and target assumptions
+ required invariants
+ known failure modes
+ verification procedure
+ performance evidence
+ portability envelope
```

It must not learn only the unusual syntax.

Repeated findings should also improve the surrounding design. If agents repeatedly add
inconsistent path validation, the preferred response may be to introduce a
`ValidatedRelativePath` type, narrow the filesystem API, add a path-confinement
micro-verifier, and update generation constraints. The system should make a weakness
harder to express rather than patch the same symptom indefinitely.

This is the desired recursive effect:

```text
finding
-> bounded repair
-> safer abstraction
-> verifier update
-> generation constraint
-> fewer reachable unsafe states
```

The recursion must not silently modify normative MNCS or MNCDS meaning. Evidence can
support an RFC; governance decides whether any proposal becomes part of the standard.

## Relationship to Forge, RAVEL, MNCS, and MNCDS

- **Forge** can route suspicious constructs to bounded providers, maintain candidate
  lineage, bind deviation records to artifacts, and preserve verifier outputs. Forge
  does not establish global correctness, independence, protected custody, or promotion.
- **Micro-verifiers** establish narrow properties within declared capability and target
  boundaries. A collection of local passes is not automatically a whole-system pass.
- **RAVEL** can coordinate controlled experiments across agents, implementations,
  compilers, machines, and trust boundaries. It may compare candidate techniques and
  verification strategies, but it cannot promote its own result.
- **MNCS** can receive bounded implementation evidence without requiring conventional
  source structure. This design note does not add a new conformance gate.
- **MNCDS** can record how intentional deviations, findings, repairs, and revalidation
  were handled during development. This design note does not alter MNCDS requirements.
- **Governance and independent evaluators** remain the authorities for standard changes,
  external evaluation, and promotion decisions.

## Initial implementation path

A bounded implementation should proceed in stages.

### Stage 1: documentation and record prototype

- define an experimental intentional-deviation record;
- bind it to artifact and environment identities;
- define finding dimensions and development dispositions;
- prohibit broad syntax whitelists and warning-only suppressions; and
- add fixtures for accepted, rejected, and `UNKNOWN` examples.

### Stage 2: local and boundary verifier pilots

Begin with narrow, explainable classes:

- path confinement;
- untrusted-data-to-command execution;
- integer-to-allocation-size flow;
- privileged-operation authorization dominance;
- secret-to-log or secret-to-network flow; and
- compiler-defined behavior for selected intentional arithmetic or dispatch patterns.

Each provider must declare capability, method, environment, limitations, and a bounded
counterexample or evidence path when possible.

### Stage 3: composition prototype

- normalize local findings without erasing provider-specific evidence;
- build bounded source-to-sink and privilege-transition graphs;
- distinguish current deployment reachability from latent composability;
- preserve unresolved edges as `UNKNOWN`; and
- test whether multiple individually modest findings form a coherent chain.

### Stage 4: controlled studies and RFC evaluation

- compare ordinary test-only generation with intent-aware verifier-assisted generation;
- measure defect discovery, false positives, repair regressions, performance retention,
  token and runtime cost, and cross-provider agreement;
- include conventional and deliberately non-orthodox implementations;
- preregister acceptance criteria; and
- use the results to inform, not bypass, the RFC and governance process.

## Non-goals

This proposal does not claim:

- perfect exploit discovery;
- proof that a system is impervious;
- automatic conversion of every warning into a safe patch;
- authority for an agent to waive failed invariants;
- that unusual code is inherently superior;
- that conventional code is inherently safe;
- that scanner agreement establishes truth;
- that local evidence establishes independent evaluation; or
- that Forge, RAVEL, or recursive learning may silently rewrite the standard.

The intended outcome is narrower: enable agents to produce and preserve more hardened
code while allowing useful, evidence-backed departures from conventional software
structure.