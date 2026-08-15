# Changelog

All notable changes are recorded here. MNCS uses semantic versioning for the
validator and explicit version identifiers for the standard.

## 0.3.0rc1 — unreleased

- Relocate canonical MNCDS specification text to
  `machine-native-complexity-development-specification`. This repository keeps
  consumed schemas, examples, and an `mncds` consumer so existing validation
  commands continue to work.
- Reconcile current GitHub Actions versions and Ruff 0.16.0 directly on current main;
  retain the cryptography `<47` bound because the proposed 49 release removes
  x86_64 macOS and 32-bit Windows support still represented by the repository's
  portability contract.

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
- Add a SHA-256-bound RAVEL 0.6 candidate-001 derivation that preserves frozen
  0.5 authority while correcting top-two planning traversal and adaptation-birth
  support provenance. Add strict derivation/compilation tests and a bounded Codex
  implementation queue; no 0.6 selection, evaluation, conformance, or promotion
  claim is made.
- Correct the Rust consumer's limitation reporting so every concurrent required
  `UNKNOWN` condition retains its issue code even after another uncertainty has
  already lowered the aggregate. Result precedence and normative text are unchanged.
- Make the non-normative Forge integration the default Codex development control plane,
  add bounded project workflows, and demote Joern to an explicitly configured optional
  legacy provider without changing any MNCS/MNCDS claim result.
- Correct release-candidate corpus and hardened Forge-entrypoint documentation, document
  the existing validator version-reporting contract, and add a Codex-ready implementation
  roadmap for larger Forge, MNCDS, empirical-study, external-review, and governance work.
- Add an experimental shared execution-assurance companion record, offline validator,
  MNCS/MNCDS combined test-evidence commands, adversarial regression coverage, draft RFC,
  and Codex implementation queue. A functional test PASS no longer implies execution
  assurance PASS; missing isolation or attestation remains UNKNOWN.
- Implement EA-NEXT-001 as an experimental typed runner execution receipt with
  canonical identity, lifecycle/output/resource observations, enforcement facts,
  optional placement linkage, assurance binding checks, CLI/API validation, and an
  adversarial corpus. This does not implement a sandbox or resolve external and
  governance blockers.
- Implement EA-NEXT-002 as an experimental immutable execution-bundle profile with
  canonical manifest identity, deterministic ZIP transport identity, bounded offline
  verification, portable path/link/archive protections, deterministic builder,
  receipt-to-bundle binding, CLI/API coverage, and adversarial fixtures. This does
  not implement isolation, custody, independence, conformance, or promotion.
- Implement EA-NEXT-005 as experimental verifier-issued execution challenges and
  bounded local replay receipts with secure nonces, exact receipt scope binding,
  single-use crash-safe ledger consumption, persisted wall-clock rollback protection,
  offline replay verification, CLI/API paths, and adversarial fixtures. This does not
  implement sandboxing, signing, custody, independence, conformance, or promotion.
- Define an additive post-RAVEL-0.6 recursive experience and causal-learning substrate
  with episodes, competing hypotheses, interventions, attribution, learned principles,
  strategy reuse, transfer gates, lineage-aware credit, an executable profile, linked
  reference records, and fail-closed negative fixtures. Frozen RAVEL evidence and the
  existing recursive-study preregistration remain unchanged.
- Document the non-normative network through which MNCS, MNCDS, MNCS Language, Forge,
  RAVEL, independent actors, and governance can refine implementations and inform future
  standard changes without allowing any tool or recursive loop to promote itself.

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
