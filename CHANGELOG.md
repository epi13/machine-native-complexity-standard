# Changelog

All notable changes are recorded here. MNCS uses semantic versioning for the
validator and explicit version identifiers for the standard.

## 0.3.0rc1 — unreleased

- Add the MNCS 0.3-rc.1 and MNCDS 0.1-rc.1 specifications without changing
  frozen historical claim semantics.
- Add versioned contract, assurance/lifecycle, threat, measurement, and development
  schemas with offline Python semantic validation.
- Add a shared release-candidate corpus, an independent Rust consumer, migration and
  governance material, and a reproducible two-epoch study.
- Keep final release, external security/privacy acceptance, independent operation,
  protected custody, and governance approval explicitly open.
- Correct the reference validator's material-change implementation to include every
  required transitive upstream claim in graph-impact and revalidation scope. This
  aligns implementation behavior with existing 0.3-rc.1 sections 7–8 and does not
  change normative text or RC identifiers.
- Add a non-normative project-owned Forge capability registry and four bounded
  Provider Protocol micro-verifiers with explicit project-level capability policy.
  These local development results do not establish conformance, independence,
  protected custody, governance approval, certification, or promotion.
- Preregister a clean RAVEL 0.6 retention-constrained adaptation epoch with
  distinct development, selection, retention, planning, and future-final
  partitions. No 0.6 implementation or evaluation is claimed, and frozen 0.4/0.5
  sources, evidence, dispositions, and promotion boundaries remain unchanged.
- Correct the Rust consumer's limitation reporting so every concurrent required
  `UNKNOWN` condition retains its issue code even after another uncertainty has
  already lowered the aggregate. Result precedence and normative text are unchanged.
- Make the non-normative Forge integration the default Codex development control plane,
  add bounded project workflows, and demote Joern to an explicitly configured optional
  legacy provider without changing any MNCS/MNCDS claim result.
- Add the experimental, non-normative execution-placement evidence profile with
  requested-versus-observed CPU/accelerator placement, residency distinction, real
  probe requirements, bounded AUTO fallback, resource measurements, strict claim
  boundaries, and an adversarial validation corpus. This does not change frozen
  MNCS/MNCDS semantics or create conformance, independence, custody, or promotion.

## 0.2.0 — 2026-07-25

- Publish normative MNCS 0.2 Attested Interoperability and RFC 0003.
- Add RFC 8785 canonical JSON, SHA-256 golden identities, Ed25519 DSSE-compatible
  multi-signature attestations, and separate cryptographic/trust outcomes.
- Add deterministic trust domains, roles, scopes, thresholds, validity, expiration,
  revocation, independent evaluators, and generator/evaluator separation.
- Add reproducible, bounded `.mncs` packages and secure extraction.
- Add Provider Protocol 0.1, a typed Python SDK, explicit bounded provider execution,
  and five honestly labeled examples.
- Add a 31-vector versioned corpus and independent Rust validator agreement while
  preserving schemas 0.1 and 0.1.1.

## 0.1.1 — 2026-07-25

- Add schema 0.1.1 evidence-derived acceptance and general gate-result records.
- Add validator-derived gates, final-status reconciliation, evidence graphs, and
  `certify` / `certify-bundle` with stable exit codes.
- Preserve frozen schema 0.1 validation with explicit reduced-assurance legacy
  certification policy.
- Bind performance evidence to sources, identities, harness, environment, build,
  corpus, samples, thresholds, and regression policy.
- Harden evidence indexing, provenance identities, paths, symlinks, file limits,
  nonfinite numbers, timestamp ordering, and extension shadowing.
- Add cumulative level schemas, migrated examples, a rule-engine self-audit,
  deterministic conformance corpus, package resources, clean-wheel testing, and
  least-privilege CI/docs jobs.

## 0.1.0 — 2026-07-25

- Publish MNCS 0.1 as an initial experimental standard.
- Define five cumulative conformance levels and evidence-weighted complexity.
- Add six JSON Schemas, an offline validator, five complete examples, tests,
  governance, RFC process, and documentation.
