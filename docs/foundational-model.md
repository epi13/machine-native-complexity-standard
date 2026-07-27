# Machine-native complexity foundation

This page is informative. RFC 0005 proposes the corresponding experimental semantics.
MNCS 0.2 and MNCDS 0.1-draft remain the current implementation and development claim
families.

## The foundation

Machine-native complexity is not a synonym for generated code. It is a deliberate
engineering arrangement in which machines may own internal implementation complexity
only when humans retain readable control over intent, limits, evidence, authority, and
lifecycle.

> Human readability is relocated, not eliminated.

A machine-native implementation should purchase a declared, measurable, operationally
useful benefit. Complexity, novelty, model preference, or code size is not itself a
benefit.

## Implementation categories

- **Human-maintained implementation:** humans are expected to understand and directly
  modify the internal structure during ordinary maintenance.
- **Generated implementation:** a machine produced some or all of the artifact. The result
  may still be normally human-maintainable.
- **Machine-optimized implementation:** a machine transformed or selected the artifact
  against an objective. This does not imply machine-owned complexity.
- **Machine-owned implementation complexity:** internal structure is expected to be
  managed mainly through regeneration, evidence, and replacement rather than routine
  manual editing.
- **Machine-native implementation:** machine-owned complexity is intentional and bounded
  by readable contracts, evidence, development controls, and operational reversibility.

Obfuscation, unverifiable output, novelty-only complexity, and artifacts with no bounded
replacement path are not machine-native engineering under this model.

## Five control planes

### Human control plane

The human control plane contains intended use, exclusions, criticality, readable
contracts, authority, acceptance policy, and risk decisions. It defines what the machine
is permitted to own and what remains prohibited.

### Machine execution plane

The machine execution plane contains candidate and release artifacts, runtime state,
dependencies, and external effects. Its internals may be difficult to maintain manually,
but its identity and supported environment remain explicit.

### Evidence plane

The evidence plane contains observations, measurements, witnesses, counterexamples,
provider assumptions, limitations, and PASS, FAIL, or UNKNOWN outcomes. It does not hide
unsupported analysis behind absence of detected defects.

### Development-control plane

The development-control plane contains the MNCDS charter, immutable baseline, generator
boundary, partitions, evaluator identities, candidate lineage, selection policy, epoch
history, and independent review.

### Operational-control plane

The operational-control plane contains release binding, monitoring, revalidation,
rollback, regeneration, replacement, and retirement. Continuing operation is not proof of
continuing conformance.

## How the claim families fit

MNCS evaluates implementation evidence. MNCDS evaluates development-process control.
Neither proves the other.

A combined display such as `MNCDS-D3 / MNCS-L4` is useful only when both results retain
their own versions, identities, statuses, scopes, issues, and limitations. An operational
acceptance decision is policy, not a third conformance result.

## Contract adequacy

A contract hash proves identity, not adequacy. The experimental contract profile asks
whether the readable contract provides enough bounded information to support the intended
evaluation without being circular or strategically narrow.

It records:

- intended use and exclusions;
- inputs, outputs, state, and transitions;
- observable and error behavior;
- malformed and adversarial input behavior;
- safety and security invariants;
- resource and timing limits;
- environment assumptions and external effects;
- compatibility requirements;
- undefined, implementation-defined, and excluded behavior;
- reference-oracle limits and tolerances;
- known ambiguities; and
- version and material-change rules.

Missing required behavior does not pass. A circular contract such as “correct behavior is
whatever the selected candidate does” fails. Material ambiguity remains UNKNOWN unless
evidence demonstrates a violation.

## Applicability and criticality

Machine-native complexity is justified only when its useful benefit exceeds its added
assurance, operational, replacement, and residual-risk cost.

Criticality should consider consequence, exposure, reversibility, safety, security,
privacy, legal impact, availability, tolerated UNKNOWN, evaluator independence, evidence
freshness, and revalidation triggers. A domain or organization may map criticality to
minimum MNCS levels and MNCDS profiles, but RFC 0005 does not impose an unevidenced
universal mapping.

The simpler-alternative principle applies: when a materially simpler implementation meets
the same contract, constraints, benefit threshold, and assurance requirements, added
machine-owned complexity needs a recorded operational justification.

## Composition

Component claims do not automatically compose. A system assurance case records an
explicit claim-dependency graph including runtime, build, service, data, evaluator, and
evidence dependencies.

The graph identifies required relationships, interface and environment compatibility,
shared evidence, correlated failure groups, freshness, and invalidation triggers. System
policy may select aggregation rules, but it may not hide a required FAIL or UNKNOWN
behind an aggregate PASS.

## Threat and measurement frameworks

The generic threat framework is documented in [Threat model](threat-model.md). It records
threat identity, affected plane, assets, actor or failure source, path, assumptions,
mitigations, evidence, detection, residual risk, owner, and revalidation triggers.

A measurement profile records baseline legitimacy, metric and operational relevance,
environment and evaluator identities, repetitions, warmup, ordering, statistics,
uncertainty, noise, outliers, hard constraints, worst-case regression, normalization,
contamination controls, and evidence freshness. Reporting only the best observed run is
not a valid repeated-measurement protocol.

## Experimental machine-readable records

RFC 0005 introduces three non-normative experimental schemas:

- `mncs-contract-profile` — contract adequacy record;
- `mncs-assurance-case` — separate MNCS and MNCDS results plus dependencies and lifecycle;
- `mncs-analyzer-result` — bounded analyzer evidence with assumptions and UNKNOWN.

They are discoverable through `mncs schema` for experimentation. They do not change MNCS
0.2 certification.

## Governance status

The project remains in bootstrap governance. Completion requires an explicit maintainer
and editor roster, succession and inactivity rules, release and signing authority, an
independent reviewer pool or a disclosed inability to form one, and continued separation
between normative semantics and reference implementations.
