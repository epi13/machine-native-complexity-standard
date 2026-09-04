# MNCS promotion boundary

Status: normative for `mncs-promotion-boundary/0.1`.

## Separation

- MNCDS describes development state: ChangeSet identity, development
  records, obligations created and resolved, evidence references, and
  whether development evidence is complete enough for evaluation.
  MNCDS never decides broad MNCS conformity.
- MNCS owns the promotion boundary: this document and the versioned
  contract in `schemas/mncs-promotion-boundary-0.1.schema.json` define
  what evidence a candidate revision must carry to cross a declared
  boundary. The owner-native evaluator,
  `scripts/mncs_promotion_evaluate.py`, applies the declaration.
- Transport (`mncs-actions`) invokes the evaluator, validates the
  `mncs.check-result/1` shape of its output, preserves receipts and
  digests, aggregates the check, and exposes the verdict. It never
  reinterprets the promotion decision.

## Lifecycle

```text
change / development activity
        |
        v
      MNCDS
development record / obligations / unresolved evidence
        |
        v
       MNCS
promotion-boundary evaluation
        |
        v
   mncs-actions
execute + aggregate + preserve  ->  PASS / FAIL / UNKNOWN
```

## Boundary declaration

A boundary names `required_evidence` (each a `check_id` plus its owning
`authority`, optionally pinned to a `contract_revision`) and
`optional_evidence` with the same shape. General evidence requirements
keep the core schema free of hard-coded family membership: any authority
can be required by naming its check.

- Every required check must `PASS`.
- A required `FAIL` is a valid negative finding -> promotion `FAIL`.
- Required `UNKNOWN`, missing, unstamped, or contract-mismatched evidence
  -> promotion `UNKNOWN`. Incomplete evidence never fabricates `PASS`.
- Optional evidence stays visible in `unresolved` and never decides;
  missing optional evidence has no effect.
- Open required MNCDS obligations block as `UNKNOWN` and are named
  exactly in `blockers`, unless listed in `tolerated_obligations`
  (explicit boundary policy, not silent tolerance).
- A `rejected` obligation with authoritative evidence is a negative
  finding -> promotion `FAIL`.

## Revision binding

Promotion binds exact revisions. The evaluator refuses branch names or
short SHAs: the subject must be a repository plus a 40-hex commit, and
the boundary declaration must belong to that repository. Required
evidence stamped for another subject is contradictory (no claim);
required evidence with no stamp is incomplete (`UNKNOWN`) when
`require_subject_binding` is true. Moving-head observations remain
observations: only reviewed, pinned evidence is promotable.

## Result shape

The evaluator emits `mncs.check-result/1` (composable with existing
aggregation) with a `promotion` extension carrying `boundary_id`,
subject, required totals, and the exact `blockers` that prevented
`PASS`, plus `references` with SHA-256 digests of every consumed
evidence document. Malformed or contradictory input establishes no
claim (`INVALID` / `NOT_ESTABLISHED` at the transport boundary):
malformed evidence is not `UNKNOWN`, valid negatives are not invalid,
and `UNKNOWN` never becomes `PASS`.
