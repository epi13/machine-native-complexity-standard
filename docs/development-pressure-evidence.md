# Development-Pressure Evidence and Promotion Boundary

Status: experimental design note for MNCS 0.2-family evolution.

MNCS defines what evidence-backed claims mean when development pressure produces a language, compiler, library, runtime, or process change. MNCDS owns the workflow; Commons exchanges records; Forge evaluates bounded candidates; the compiler may emit capability gaps.

## Typed evidence relationships

Pressure evidence may use:

- `supports_pressure`
- `resolves_pressure`
- `supports_resolution`
- `contradicts_resolution`
- `replicates_resolution`
- `invalidates_resolution`
- `supports_promotion`

Each relationship is scoped to a claim, contract, policy, environment, and identity.

Existing meanings remain unchanged:

- PASS supports the declared claim for the declared scope;
- FAIL contradicts it or leaves an explicit obligation unmet;
- UNKNOWN means evidence is insufficient, unavailable, or unresolved.

None means universal correctness.

## Evidence bundles

A candidate or cross-repository ChangeSet should carry pressure/proposal/ChangeSet identities; exact revisions and assembled final-tree identity; contract, policy, compiler, evaluator, and tool revisions; reproducer/corpus/input digests; affected profiles, backends, workers, and environments; raw observations and derived claims; negative checks and disagreements; per-surface statuses; unresolved fields and non-claims; and provenance/attestations where required.

Evidence is content-addressed and append-only. Replications, corrections, and invalidations amend the graph rather than rewrite history.

## Promotion boundary

A promotion record names the candidate or ChangeSet, authority level, exact scope and contract, policy and evaluator, evidence set, unresolved unknowns, compatibility conditions, and rollback/regeneration conditions.

Component PASS does not create system PASS. Aggregate claims require an explicit claim/dependency graph and evidence for the aggregate obligation. When an upstream claim is invalidated, dependent claims become stale or are recomputed according to policy; they must not retain unexplained PASS.

The authority path is:

`local experiment -> candidate -> family-visible experimental -> verified standard -> core guarantee`

Each transition is a new scoped claim with new evidence requirements. Untested backends and independent evaluators remain UNKNOWN.

## Initial conformance target

The first target is fixture interoperability:

1. independent producers emit equivalent canonical pressure records;
2. consumers preserve identity, scope, and explicit unknowns;
3. Forge-style evaluation attaches evidence without changing MNCS meaning;
4. Commons-style publication does not imply acceptance;
5. invalidation/replication amendments update dependent claim state deterministically.

No implementation should claim full distributed governance or standard promotion until these fixtures and negative cases exist.
