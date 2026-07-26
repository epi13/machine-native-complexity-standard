# RFC 0002: Evidence-Derived Conformance

Status: Accepted for validator and schema patch 0.1.1
Standard family: MNCS 0.1 (experimental)
Package and schema release: 0.1.1

## Summary

MNCS 0.1.1 separates acceptance policy from observed evidence. A new manifest says
which gates and thresholds are required, then refers to content-addressed evaluator
records through an authoritative evidence index. The validator binds those records
to the candidate, reference, contract, evaluator, and environment; derives every
gate; aggregates the claimed level; and reconciles the declared final status.

The normative MNCS family remains 0.1. This is a compatible hardening patch, not a
new assurance level or an accredited certification regime.

## Problem

The original 0.1 manifest stored fields such as `behavioral_pass`,
`compiler_matrix_pass`, and `measurement_valid` inside `acceptance_policy`. The
validator mostly aggregated those values. A producer could therefore copy `PASS`
into the manifest without supplying a corresponding observation. Hashing that
manifest only proves which assertion was hashed; it does not prove that an
evaluator made the observation, that the evaluator examined this candidate, or
that a threshold calculation was sound.

Content hashes alone are insufficient because a perfectly hashed record can still:

- name another candidate, reference, contract, tool, or environment;
- contain an empty positive assertion;
- summarize samples inconsistently;
- refer to an identity with no indexed identity record;
- become unreachable or ambiguous inside a duplicate-path evidence index.

## Policy, observation, and computation

The 0.1.1 manifest has three deliberately separate layers.

1. Acceptance policy declares cumulative gates, UNKNOWN handling, conflict policy,
   objective semantics, thresholds, sample requirements, and regression limits.
2. Evidence observations are immutable, indexed records. General gate results
   report evaluator observations; performance, invariant, provenance, and identity
   records carry domain-specific bindings.
3. Computed conformance is validator output. It includes per-gate decisions,
   evidence used and excluded, conflicts, claimed-level status, final status,
   certification eligibility, warnings, and an evidence dependency graph.

The policy cannot contain authoritative observed PASS values.

## Evidence graph and identity

Every manifest reference resolves through a unique evidence-index ID. Index records
bind ID, kind, relative path, SHA-256 identity, media type, contract, and candidate
where applicable. Duplicate IDs, conflicting path/hash pairs, missing references,
path escape, and symlink evidence are rejected. Unreachable indexed evidence is
reported according to the index policy.

Evaluator, generator, environment, toolchain, build, harness, and corpus hashes
must match indexed identity records. A random syntactically valid hash has no
standing by itself.

## Deterministic gate aggregation

Each required gate must have usable evidence. Multiple observations aggregate as:

`FAIL` > `UNKNOWN` > `PASS`

An empty set derives `UNKNOWN` and is a semantic error for a required gate.
Conflicting providers are surfaced explicitly and rejected by the 0.1.1 policy.
UNKNOWN never becomes PASS. The declared final status must exactly equal the
computed claimed-level status.

Performance records are special observations shared by three derived gates:
measurement validity, useful-benefit threshold, and worst-regression policy. The
validator recomputes sample counts, summaries, ratios, and statuses.

## Cumulative levels

Level requirements are conditional in the 2020-12 manifest schema:

- L1 requires behavioral and strict compiler/language evidence.
- L2 adds safety, resource bounds, malformed-input/fuzz evidence, and mutation.
- L3 adds structural invariants, provider assumptions, and bounded aggregation.
- L4 adds bound performance observations and the three derived performance gates.
- L5 adds independent holdout, reproducibility, locked regeneration, provenance,
  rollback, immutable indexing, and post-certification identity checking.

Lower levels do not carry placeholder UNKNOWN records for higher-level artifacts.

## Legacy compatibility

Frozen 0.1 schemas remain packaged. A schema 0.1 bundle is validated without being
rewritten or silently reinterpreted and reports
`legacy_self_asserted_acceptance: true`. Ordinary validation can remain structurally
successful. Certification and `--require-pass` reject the legacy assurance model
with exit code 3 unless `--allow-legacy` is explicit. An override remains visibly
reduced-assurance.

## Certification semantics

`validate` answers whether structure, bindings, evidence mechanics, and the
declared/computed reconciliation are valid. A valid bundle may compute FAIL or
UNKNOWN. `certify` additionally requires an eligible PASS.

A validator PASS is scoped only to the declared contract and environment. It is
not an accreditation, legal certification, general security warranty, or proof
outside those bounds.

## Security consequences

The implementation remains offline and never executes, imports, or opens network
resources from evidence. It rejects traversal and symlink evidence, bounds JSON and
index sizes, hashes regular files through no-follow descriptors, detects change
during hashing, rejects nonfinite values, validates timestamp ordering, prevents
extension shadowing, and makes aggregation precedence unambiguous.

SHA-256 provides content identity, not signer identity or freshness. Signed
attestations and transparency systems remain future work.

## Rejected alternatives

Keeping authoritative statuses in policy was rejected because it preserves the
self-assertion flaw. Merely requiring more hashes was rejected because hashes do
not establish semantic binding. Executing evidence was rejected because it expands
the trust and attack surface. Invented comparison weights were rejected because
they hide stakeholder policy. Treating a higher MNCS level as a performance number
was rejected because assurance strength and benefit are different dimensions.

## Compatibility and rollout

Primary examples move to schema 0.1.1; one explicit legacy example remains.
Runtime schemas move into package resources and are verified from a clean wheel.
The conformance corpus provides deterministic valid, rejected, unknown, legacy,
binding, ambiguity, numeric, timestamp, extension, and filesystem cases.
