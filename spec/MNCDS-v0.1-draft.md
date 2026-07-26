# Machine-Native Complexity Development Specification 0.1 (Draft)

MNCDS 0.1 is a proposed, experimental, tool-neutral companion to the Machine-Native Complexity Standard. Normative terms use the meanings defined in `normative-language.md`.

MNCDS governs the process used to create, evaluate, select, release, regenerate, replace, and retire machine-native implementations. MNCS governs the evidence required to accept such an implementation. An MNCDS claim MUST NOT be represented as an MNCS conformance claim, and an MNCS claim MUST NOT imply compliance with MNCDS unless both are separately established.

> Machine-owned implementation complexity requires human- and machine-auditable development control.

## 1. Scope

MNCDS applies when a development process intentionally permits generated or machine-optimized implementation structure to exceed ordinary human-maintainability limits in exchange for a declared measurable benefit.

MNCDS standardizes lifecycle records, authority boundaries, evaluation discipline, selection controls, provenance, reproducibility, rollback, and regeneration. It does not prescribe a programming language, model, optimizer, analyzer, benchmark framework, compiler, proof system, or orchestration platform.

A process MAY use code-generating models, evolutionary search, superoptimization, synthesis, automated repair, graph transformation, reinforcement learning, compiler optimization, program induction, or combinations of these methods.

## 2. Required identities and records

Every conforming process MUST assign stable content or canonical identities to:

- the readable contract;
- the reference behavior or baseline implementation;
- the declared environment;
- the threat and misuse model;
- the objective function and constraints;
- the generator and its effective configuration;
- each materially evaluated candidate;
- each evaluator, analyzer, benchmark, and measurement method;
- the development, validation, and holdout partitions;
- the selection policy;
- the selected candidate;
- the resulting MNCS bundle or package, when an MNCS claim is made.

The process MUST preserve an append-only development record sufficient to reconstruct which identities and policies were in force at each decision point. Correcting a record MUST create a new record that references the superseded record; it MUST NOT silently rewrite history.

## 3. Roles and authority boundaries

A development record MUST identify these logical roles:

- **Contract authority:** approves the readable contract, limits, and acceptance intent.
- **Generator authority:** operates or configures candidate generation.
- **Evaluator authority:** controls development-time tests, analyzers, and measurements.
- **Selection authority:** applies the candidate-selection rule.
- **Release authority:** authorizes deployment or publication.
- **Independent reviewer:** evaluates the selected candidate using protected evidence for profiles that require independence.

One person, organization, or system MAY hold multiple roles unless a claimed profile prohibits it. All overlaps MUST be disclosed.

The generator MUST NOT have undeclared authority to modify the contract, reference behavior, evaluator, acceptance policy, safety limits, holdout evidence, or release criteria. Any authorized change to those items MUST begin a new development epoch and receive a new identity.

## 4. Development charter

Before materially evaluating candidates, the process MUST create a development charter containing:

- problem statement and intended use;
- readable contract and exclusions;
- declared environment and resource limits;
- threat model and prohibited behavior;
- baseline implementation or reference behavior;
- useful-benefit objective;
- mandatory constraints and hard rejection gates;
- evaluation methods and data partitions;
- candidate-selection policy;
- planned MNCDS profile and MNCS level, if any;
- rollback, regeneration, and retirement ownership.

The useful-benefit objective MUST be measurable. Complexity, novelty, model preference, or code size alone MUST NOT count as a useful benefit unless the charter explains why the metric is operationally valuable.

The process MUST record any later charter change, its rationale, affected evidence, and whether previous measurements remain valid. A material change MUST begin a new epoch.

## 5. Baseline and environment lock

Before candidate search begins, the process MUST preserve an immutable baseline and its evaluation results under the declared environment.

The baseline record MUST include:

- source or artifact identity;
- build and dependency identities;
- environment identity;
- evaluator identities;
- functional, safety, resource, and performance results;
- known failures and UNKNOWN outcomes.

A candidate MUST NOT be credited with improvement against a baseline measured under materially different conditions unless the difference is declared and justified. The comparison method MUST prevent a weaker, stale, or intentionally degraded baseline from creating a false benefit.

## 6. Evaluation partitioning

The process MUST distinguish at least:

- **development evidence**, which MAY guide generation and tuning;
- **selection evidence**, which MAY rank candidates under the predeclared policy;
- **protected holdout evidence**, which MUST remain inaccessible to the generator and ordinary ranking process when required by the claimed profile.

Partition identities and access rules MUST be recorded before use. Evidence that has influenced generation or selection MUST NOT later be described as protected holdout evidence for the same claim.

A leaked, inspected, inferred, or repeatedly queried holdout MUST be marked contaminated. The process MUST replace it or downgrade the claim.

## 7. Candidate-generation envelope

The development charter MUST declare the generator's permitted inputs, outputs, tools, network access, filesystem access, executable authority, and mutation scope.

The generator MUST operate within explicit resource and time bounds. Unbounded search MUST NOT be represented as controlled development.

Each materially evaluated candidate MUST have:

- a stable identity;
- parent or source lineage;
- generator and configuration identity;
- generation time or sequence position;
- declared transformations;
- build status;
- evaluation status;
- disposition.

A stochastic generator SHOULD record seeds and sampling parameters. When exact regeneration is not possible, the process MUST state the reproducibility level and preserve enough information to reproduce the distribution, search policy, or candidate family rather than claiming bitwise regeneration.

## 8. Experiment ledger

The process MUST maintain an append-only experiment ledger.

For each materially evaluated candidate, the ledger MUST record:

- candidate identity and lineage;
- active charter and epoch identity;
- evaluator and environment identities;
- objective values and constraint outcomes;
- PASS, FAIL, and UNKNOWN results;
- measurement uncertainty where applicable;
- rejection, retention, promotion, or selection reason;
- operator or automated decision identity.

The process MAY summarize candidates rejected before material evaluation, but it MUST define the summarization rule. It MUST NOT omit evaluated candidates merely because they weaken the apparent success rate or reveal undesirable selection pressure.

Evaluator crashes, unsupported syntax, timeouts, missing data, and inconclusive analysis MUST be recorded as UNKNOWN or operational error. They MUST NOT be converted to PASS by omission or by the absence of a detected defect.

## 9. Progressive evaluation

Candidate evaluation SHOULD proceed through increasingly expensive gates, such as:

1. build and format checks;
2. contract and regression tests;
3. malformed-input and safety tests;
4. structural or semantic analysis;
5. fuzz, property, symbolic, or model-based testing;
6. resource and performance measurement;
7. adversarial and holdout evaluation;
8. independent verification.

A later gate MUST NOT erase an earlier FAIL. A candidate MAY be repaired and re-enter as a new identity.

Performance claims MUST use a declared measurement protocol with sufficient repetitions, warmup policy, environment controls, summary statistics, and uncertainty treatment. The selection process MUST NOT choose a candidate from noise and then report only its best measurement.

## 10. Candidate selection

The candidate-selection rule MUST be recorded before final holdout evaluation.

The rule MUST state:

- hard rejection gates;
- objective metrics;
- metric direction and weighting;
- tie-breaking behavior;
- treatment of UNKNOWN;
- minimum useful-benefit threshold;
- maximum accepted regressions;
- whether human judgment is permitted and how it is recorded.

Selection MUST apply the declared rule to the recorded candidate set. A post hoc change to the rule MUST begin a new selection epoch and MUST be disclosed.

The selected candidate MUST satisfy all mandatory constraints. A superior aggregate score MUST NOT compensate for failure of a hard safety, correctness, legal, privacy, or resource limit.

The process MUST preserve enough rejected-candidate information to audit why the selected candidate won and whether the search exploited evaluator weaknesses.

## 11. Independent verification

When the claimed profile requires independence, the selected candidate MUST be evaluated by an independent reviewer using fresh or previously inaccessible evidence.

The independent evaluator MUST differ from the generator and ordinary ranking process by executable identity, immutable configuration, key identity, or organizational control sufficient to prevent the generator from silently shaping the final result.

Independent verification MUST include:

- confirmation of candidate and contract identities;
- confirmation of environment and evaluator identities;
- protected holdout or fresh challenge evidence;
- explicit PASS, FAIL, and UNKNOWN outcomes;
- confirmation that the predeclared selection rule was followed;
- review of material role conflicts and deviations.

Failure of independent verification MUST block the associated profile claim. Repair creates a new candidate identity and requires reevaluation.

## 12. MNCS binding

A project claiming MNCS conformance for a selected candidate MUST produce an MNCS manifest or package whose candidate, contract, environment, evidence, and policy identities agree with the final MNCDS records.

MNCDS process evidence MAY be included in or referenced by an MNCS evidence graph, but the two conformance results MUST remain distinguishable.

A truthful combined claim SHOULD use the form:

`MNCDS-D<profile> / MNCS-L<level>`

A process record MUST NOT state or imply that disciplined development proves implementation correctness. An MNCS validator result MUST NOT state or imply that the candidate was developed under MNCDS controls unless those controls were separately validated.

## 13. Recursive improvement and development epochs

Evidence from one development epoch MAY be used to improve a generator, evaluator, analyzer, benchmark harness, or search strategy in a later epoch.

Recursive improvement MUST satisfy all of these requirements:

- the prior and updated toolchains receive distinct identities;
- the evidence used for improvement is identified;
- the improvement objective and observed failure modes are recorded;
- protected holdout evidence MUST NOT be reused as development evidence for the same acceptance claim;
- the updated harness or evaluator MUST be revalidated against its own regression or conformance corpus;
- historical claims remain bound to their original toolchain and evidence identities;
- candidate results from incompatible epochs MUST NOT be pooled without a declared normalization method.

A process MAY use differences between competing implementations, analyzers, or experimental ideas to improve the original harness. Such recursive use SHOULD preserve disagreement cases as regression fixtures. Cases that cannot be resolved MUST remain UNKNOWN rather than being forced into agreement.

## 14. Release and operational controls

Before deployment or publication, the process MUST bind the selected candidate to:

- release artifact identity;
- build and packaging procedure;
- supported environment;
- MNCS package or manifest identity, when applicable;
- known limitations and UNKNOWN outcomes;
- rollback artifact and procedure;
- monitoring signals and thresholds;
- responsible release authority.

A release MUST NOT broaden the contract or supported environment beyond the evaluated scope.

Operational monitoring MUST distinguish observed failure, suspected drift, unavailable evidence, and normal operation. Absence of a detected incident MUST NOT be treated as proof of continuing conformance.

## 15. Regeneration, replacement, and retirement

The process MUST preserve a regeneration specification containing:

- generator and toolchain identities;
- required inputs and access boundaries;
- build and evaluation procedures;
- expected stochastic or deterministic reproducibility level;
- selection policy;
- required credentials or trust material by reference;
- fallback and rollback instructions.

For profile D4, the project MUST perform and record a regeneration or replacement drill. The drill MAY use a non-production environment but MUST exercise the documented control path sufficiently to reveal missing dependencies, inaccessible evidence, or irreproducible steps.

The process MUST declare retirement triggers, including contract change, environment drift, dependency obsolescence, evidence invalidation, security findings, repeated operational UNKNOWN, or inability to regenerate.

Retirement MUST preserve the final artifact identity, reason, replacement identity when applicable, and affected claims. Historical records MUST remain immutable.

## 16. Development conformance profiles

Profiles are cumulative.

### MNCDS-D1 — Controlled generation

D1 requires:

- development charter;
- immutable baseline;
- bounded generator authority;
- stable candidate identities and lineage;
- experiment ledger;
- explicit PASS, FAIL, and UNKNOWN;
- recorded candidate-selection rationale.

### MNCDS-D2 — Reproducible experimentation

D2 adds:

- pinned development environment;
- identified evidence partitions;
- reproducible or statistically characterized generation;
- declared measurement protocol and uncertainty;
- versioned evaluators and harness regression corpus;
- preserved epoch boundaries.

### MNCDS-D3 — Independent selection

D3 adds:

- predeclared selection rule;
- protected holdout or fresh challenge evidence;
- independent final evaluator;
- audited role separation and conflicts;
- verification that selection followed the declared rule;
- binding to an MNCS candidate package when an MNCS claim is made.

### MNCDS-D4 — Operational regeneration

D4 adds:

- release identity and environment binding;
- monitoring thresholds;
- tested rollback;
- regeneration or replacement drill;
- explicit retirement triggers and records.

A profile claim MUST identify the MNCDS version, development-record identity, selected-candidate identity, and evaluation time. Claiming D4 means satisfying D1 through D4.

## 17. Deviations and UNKNOWN

A SHOULD-level deviation MUST include a recorded rationale and risk assessment.

Missing required records, inaccessible evidence, unsupported analysis, unresolved identity mismatch, contaminated holdout, or unverified role independence MUST produce FAIL or UNKNOWN according to the applicable rule. They MUST NOT silently satisfy a profile.

A policy MAY reject UNKNOWN or require human review. It MUST NOT convert UNKNOWN to PASS.

## 18. Privacy and restricted disclosure

A project MAY protect proprietary prompts, datasets, source code, model weights, or credentials. Restricted material MUST still receive stable identities and access-boundary descriptions.

Redaction MUST NOT broaden a claim. A reviewer unable to inspect required evidence MUST report UNKNOWN unless an accepted independent attestation or privacy-preserving proof establishes the requirement.

## 19. Tool and vendor neutrality

No model vendor, agent framework, analyzer, compiler, graph database, proof assistant, benchmark service, or orchestration platform is normative.

Joern, compiler CFG analysis, LLVM passes, abstract interpretation, symbolic execution, fuzzing, model checking, proof assistants, custom analyzers, and independent combinations MAY serve as evaluators or providers.

Unsupported operations MUST be reported as unsupported or UNKNOWN, never PASS.

## 20. Claim limitations

MNCDS conformance demonstrates that the declared development process followed the specified controls within its recorded scope. It does not prove that:

- the contract is complete;
- the objective is socially desirable;
- the evidence is truthful;
- the implementation is free from defects;
- independent parties are honest;
- deployment outside the declared environment is safe;
- regeneration will remain possible indefinitely.

MNCDS 0.1 is a draft proposal for experimentation and public review. It is not an accredited standard or blanket assurance claim.
