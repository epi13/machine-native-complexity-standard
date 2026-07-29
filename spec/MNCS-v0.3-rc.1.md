# Machine-Native Complexity Standard 0.3-rc.1

Status: release-candidate proposal under Draft RFC 0005. This document is complete
enough to implement, but it is not Accepted or Final. Normative terms use RFC
2119/8174 meanings as described in `normative-language.md`.

## 1. Scope and result model

MNCS 0.3 defines controlled system assurance for newly issued claims. It extends,
without replacing, MNCS 0.2 evidence identities, attestations, trust policies,
packages, provider boundaries, and implementation-conformance results.

The only MNCS conformance results are `PASS`, `FAIL`, and `UNKNOWN`. `FAIL` dominates
`UNKNOWN`; `UNKNOWN` dominates `PASS`. Missing required evidence is `UNKNOWN`.
Unsupported required behavior is `UNKNOWN`, never `PASS`. An operational disposition
such as `accepted`, `rejected`, or `review_required` is a policy decision and MUST NOT
be represented as an MNCS or MNCDS result.

MNCS and MNCDS evaluate different facts. A combined assurance case MUST retain their
versions, result identities, scopes, statuses, issues, and limitations separately. It
MUST NOT calculate or store a third combined conformance score.

## 2. Compatibility and implementation conformance

MNCS 0.1, 0.1.1, and 0.2 artifacts remain valid under their original rules. Their
schema identifiers and validation behavior MUST remain addressable. An implementation
MUST NOT rewrite or automatically upgrade a historical claim.

An MNCS 0.3 implementation:

1. MUST validate Draft 2020-12 schemas and the semantic rules in this document;
2. MUST operate offline during ordinary validation;
3. MUST NOT execute candidates, providers, analyzers, generators, compilers,
   benchmarks, services, or evidence binaries during ordinary validation;
4. MUST distinguish `PASS`, `FAIL`, `UNKNOWN`, `UNSUPPORTED`, invalid input, and
   implementation or operational error in machine-readable output;
5. MUST reject unknown core fields and unsupported core schema versions;
6. MUST preserve all required `FAIL` and `UNKNOWN` results;
7. MUST expose the supported schema and standard versions; and
8. MUST use stable normalized rule identifiers.

Reference validators and corpora are non-normative implementations. Implementation
independence requires a separately implemented decision path that neither imports,
invokes, nor reuses generated decision code from another validator. A different
executable identity can be proven locally. Independent operation and organizational
independence require external evidence and MUST NOT be inferred from implementation
language.

## 3. Normative record family

The MNCS 0.3-rc.1 normative machine-readable family is:

- `mncs-contract-profile-0.3` for contract adequacy;
- `mncs-assurance-case-0.3` for component and system claims, dependencies, freshness,
  material change, revalidation, supersession, replacement, rollback, retirement,
  migration, and operational disposition;
- `mncs-threat-record-0.3` for portable threat facts; and
- `mncs-measurement-profile-0.3` for portable measurement protocols.

The assurance case intentionally combines related lifecycle concerns. Implementations
MUST NOT require additional unversioned side records to interpret its core semantics.

Language evidence profiles, the MNEA/Clang provider, Wave records, host/cohort records,
and composed-system schemas with `experimental` identifiers remain non-normative.

## 4. Contract adequacy

Every newly issued MNCS 0.3 claim MUST bind a contract profile with a distinct
`profile_id`, the evaluated `contract_id`, and `contract_content_identity`.

The profile MUST record intended use and exclusions; inputs, outputs, state and state
transitions; observable behavior, errors, malformed and adversarial inputs; external
effects; safety and security invariants; applicable resource and timing limits;
environment assumptions; compatibility; undefined, implementation-defined and excluded
behavior; oracle identity and limits; ambiguities; versioning; findings; evidence; and
limitations.

Correctness defined circularly as whatever the candidate does MUST produce `FAIL`.
Missing malformed-input behavior or a missing applicable resource limit MUST produce
`FAIL`. An incompatible environment assumption demonstrated by evidence MUST produce
`FAIL`. A material ambiguity without a demonstrated violation MUST produce `UNKNOWN`.
A direct contradiction or demonstrated violation MUST produce `FAIL`.

The overall contract result MUST equal the dominant required finding. `PASS` requires
every required finding to be `PASS` and every mandatory section to be applicable or
explicitly justified as not applicable.

Changed canonical contract bytes get a new content identity. A material change MUST
also receive a new logical contract identity and an evidence-impact assessment.

## 5. Evidence identities, trust, attestations, and packages

MNCS 0.2 canonical JSON, content identities, DSSE/Ed25519 baseline, trust-policy, and
reproducible-package rules remain applicable. An identity authenticates bytes, not
adequacy or truth. A signature does not imply trust. Trust does not imply conformance.

Every referenced core record MUST resolve by identity within the supplied offline
resolution set or be explicitly marked unavailable. Unavailable required evidence is
`UNKNOWN`. Conflicting bytes for one identity MUST produce invalid input.

MNCS 0.3 attestations MUST state the predicate and schema version. A verifier MUST
reject downgrade substitution when an expected 0.3 predicate is replaced with a 0.2
predicate. A 0.2 package MAY be referenced by a 0.3 assurance case, but its embedded
implementation result remains 0.2.

## 6. Components, systems, and claim-dependency graphs

An assurance case MUST declare whether its subject is a component or system. A system
MUST contain an explicit claim graph. Each claim node records identity, subject,
contract, environment, MNCS version and level, status, result identity, scope, issues,
limitations, freshness, and retirement state.

Each edge records source and target claims; relation; required/optional status;
interface and environment compatibility; shared evidence; correlated-failure groups;
and invalidation triggers. Referenced nodes and groups MUST exist. Claim dependencies
MUST be acyclic.

For a required edge, target `FAIL`, compatibility `FAIL`, or a retired target makes the
source `FAIL`. Target `UNKNOWN`, compatibility `UNKNOWN`, stale evidence, or an
unresolved target makes the source `UNKNOWN` unless another required input fails.
Optional `FAIL` or `UNKNOWN` MUST be retained as a limitation but does not by itself
change the source result. A declared source status inconsistent with propagation is
invalid.

Mixed MNCS levels and MNCDS profiles MUST be preserved per claim. Aggregation MUST NOT
relable a weaker result as a stronger level or profile.

## 7. Freshness, material change, and invalidation

Every claim and evidence binding MUST record `evaluated_at`, `valid_until` or an
explicit no-default-expiry policy, and revalidation triggers. Evidence past
`valid_until` is stale and required use is `UNKNOWN`. Revocation, a retired dependency,
or a demonstrated invalid binding is `FAIL`.

A material-change assessment MUST consider artifact, source, toolchain, environment,
policy, contract, provider, evaluator, dependency, operational, and evidence-custody
changes. Each changed dimension records old/new identities, materiality, rationale, and
affected claims.

A material change invalidates all claims reachable through declared dependency or
invalidation paths. A policy MAY require broader invalidation but MUST NOT require less
than graph impact. An evidence-impact assessment MUST list retained, invalidated, and
newly required evidence.

## 8. Partial and full revalidation

Partial revalidation is permitted only when the material-change and evidence-impact
assessments are present; every affected claim and dependency path is covered; retained
evidence is fresh and compatible; no affected required claim is retired or unresolved;
and statuses are recomputed.

An omitted affected claim, stale retained evidence, changed contract without adequacy
reevaluation, or incomplete dependency closure makes partial revalidation insufficient
and the affected result `UNKNOWN`. Full revalidation MUST reevaluate contract adequacy,
all required claims, dependencies, freshness, and lifecycle bindings.

## 9. Supersession, replacement, rollback, and retirement

Supersession MUST identify the prior case, reason, effective time, and historical
usability. It does not alter historical bytes or results.

A replacement MUST identify old/new artifact and claim identities, compatibility
evidence, evaluation result, and effective time. It MUST create a new claim identity.

A rollback MUST bind active release, rollback artifact, procedure, environment, test
evidence, and result. An artifact for another release/environment is `FAIL`. Untested
or stale rollback evidence is `UNKNOWN`.

Retirement MUST identify claim, reason, effective time, affected claims, and replacement
when present. A retired claim MUST NOT support a current `PASS`; historical displays MAY
show its original result with `retired: true`.

## 10. Separate assurance presentation

The top-level assurance case contains separate `mncs` and `mncds` result objects. The
MNCDS object MAY be null. Missing MNCDS history MUST NOT change the MNCS result.

An optional `MNCDS-D3 / MNCS-L4` label is presentation only and MUST agree with the
objects. Operational disposition records policy, decision, rationale, authority, and
time and MUST NOT contain a conformance status field.

## 11. Threat, measurement, criticality, and applicability

A threat record MUST identify threat, control plane, assets, actor/source, preconditions,
path, assumptions, mitigations/evidence, detection, residual risk, owner, revalidation,
privacy impact, status, and limitations. Identifying mitigation does not prove it.

A measurement profile MUST bind baseline, candidate, metric, unit, direction,
operational relevance, environment, hardware, software, evaluator, benchmark, warmup,
sample count, repetitions, ordering, randomization, summaries, uncertainty, noise,
outliers, hard constraints, worst regression, Pareto treatment, normalization,
contamination, useful-benefit threshold, and freshness. Best-run-only reporting is
`FAIL`.

Criticality and applicability labels are portable facts. Universal mappings to MNCS
levels or MNCDS profiles are external policy and MUST be separately identified.

## 12. Provider and operational boundaries

Provider Protocol 0.1 remains the explicit execution boundary. Ordinary validation
MUST NOT invoke a provider. Unsupported provider methods yield `UNSUPPORTED` or
`UNKNOWN`.

Offline validation MUST resolve only supplied files and packaged schemas. It MUST NOT
fetch schemas, revocations, transparency logs, dependencies, or evidence implicitly.

## 13. Security and privacy

Implementations MUST defend against claim broadening, UNKNOWN promotion, downgrade and
schema confusion, identity substitution, canonicalization ambiguity, stale evidence
and replay, superseded-evidence reuse, dependency omission, correlated-failure
concealment, false independence/custody, result collapse, malicious references,
resource exhaustion, path traversal, unsafe archives, and implicit execution/network.

Redaction is not verification. Required hidden evidence remains `UNKNOWN` unless an
accepted version-compatible proof or attestation establishes the fact. Records SHOULD
minimize private data and MUST identify redaction assurance effects.

## 14. Version negotiation and migration

Implementations MUST dispatch on exact schema identifier and declared version. Unknown
versions are `UNSUPPORTED`, not invalid evidence and not `PASS`. When 0.3 is required,
supplying only 0.2 is a distinct downgrade.

Migration from 0.2 is optional. A claim may remain historical 0.2, be referenced as a
0.2 component in a 0.3 case, or be reevaluated to create a new 0.3 identity. Wrapping
does not upgrade. Missing historical facts remain `UNKNOWN`.

## 15. Conformance statement

A conforming implementation MUST state supported schemas/rules, unsupported rules,
executable identity, corpus results, and disagreements. Local implementation diversity
does not establish independent operation, organizational independence, protected
custody, governance approval, accreditation, or final release.
