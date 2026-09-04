# MNCS repository-owned promotion (self-dogfood)

Status: implemented (promotion boundary `mncs-promotion`).

MNCS dogfoods its own promotion semantics: the repository consumes the
pinned `mncs-actions` reusable family verification through a
repository-owned boundary, evaluated by this repository's own evaluator.
This document describes the implementation, not an aspiration.

## What promotion decides here

Promotion evaluates the **recorded candidate revision**
(`promotion/candidate.json`), not HEAD. The candidate names an exact
immutable commit plus the obligation set that describes it. (MNCS carries
no MNCDS development record of its own process; `record` is null by
explicit design. MNCS development evidence is the owner-native validation
gate below, and MNCDS contributes the obligation lifecycle.)

## Required evidence

The boundary (`promotion/mncs-promotion.boundary.json`) requires exactly:

- `mncs-validation` (contract `0.2`): the owner operation the family
  producer contract names (`mncs-standard-validate`: the owner
  `mncs_validator` package over `examples/minimal/manifest.json`),
  projected through the pinned transport adapter (envelope only).
- `mncds-obligations` (contract `mncds-obligation-record/0.2`): the
  candidate's obligation set, evaluated by `mncds evaluate-obligations`
  from the pinned MNCDS revision. A required open obligation holds the
  boundary at UNKNOWN; an authoritative required rejection holds it at
  FAIL; malformed input establishes no claim.
- `promotion-boundary` (contract `0.1`): this evaluation's own output.
  The evaluator notes and skips the self entry -- a result cannot be its
  own input -- while aggregation enforces the claim's presence (see
  `docs/promotion-boundary.md`, self-reference). No self-approval is
  fabricated: the verdict is decided solely by the other two checks
  (`required_total` excludes self; asserted in tests and CI vectors).

The authority map (`promotion/authority-map.json`) is repository-owned
and covers exactly these three checks.

## Who owns what

- MNCS owns promotion-boundary semantics: this boundary, the
  `mncs-promotion-boundary/0.1` contract, and the owner-native evaluator.
- MNCS also owns its validation evidence (the validator package).
- MNCDS owns the obligation lifecycle and its evaluation.
- `mncs-actions` transports: the reusable workflow (pinned, never
  `@main`), envelopes, claim validation, aggregation, gating.
- Commons relates the resulting claim without deciding it.

## Self-dogfood revision policy

The promotion command runs the **working-tree evaluator**, because the
evaluator under test is this repository itself: pinning an older
evaluator would test old code instead of the change. Exact revision
binding is preserved mechanically -- `--producer-revision` names the
exact commit whose evaluator ran -- so a verdict is always bound to the
code that produced it.

## Compatibility observation vs promotion

Producer canaries observe what pinned family checkouts currently produce
and stay UNKNOWN while blockers stand; they never imply promotability.
The `promotion` workflow here is an actual gate (`fail-on-unknown: true`):
green means the candidate genuinely satisfied the boundary. The `vectors`
job proves the gate bites: 13 adversarial vectors over the real boundary
and real evidence (pass universe, no-self-approval, open, rejected,
malformed/duplicate obligations, wrong commit, moving ref, missing
evidence, tampered authority, duplicate checks, stale revision, forged
digest with byte-rebinding control).

## Pins (immutable reviewed revisions)

- Reusable workflow + transport: `4b13265...` (mncs-actions main,
  post PR #19 duplicate-binding hardening).
- MNCDS validator: `7020134...` (MNCDS main, repository-owned
  promotion merge).

Advance only after the upstream merge lands, in a follow-up change, then
re-run CI against the merged revision.
