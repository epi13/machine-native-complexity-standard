# Release-candidate readiness checklists

Checked items are internally reproducible. Approval fields remain OPEN until the
required person or organization acts.

## RFC approval

- [x] RFC 0004 and 0005 remain Draft.
- [x] Decision-ready rules, alternatives, compatibility, security, migration, and
  test obligations are recorded.
- [x] Public review package is assembled.
- [ ] Two-week public review: **OPEN**.
- [ ] Two non-conflicted approvals when available: **OPEN**.
- [ ] Maintainer decision: **OPEN**.

## Schema and corpus freeze

- [x] Stable RC identifiers and Draft 2020-12 self-validation.
- [x] Top-level and packaged schema copies agree.
- [x] Strict core unknown-field behavior.
- [x] Positive, negative, boundary, identity, downgrade, unsupported, and tri-state
  vectors.
- [x] Python and independent Rust corpus consumers.
- [x] Zero corpus disagreements.
- [ ] Independent reviewer confirms freeze hashes: **OPEN**.

## Validator agreement

- [x] Ordinary validation executes no providers, analyzers, generators, candidates,
  compilers, benchmarks, or evidence binaries.
- [x] Rust does not import, invoke, or reuse Python decision code.
- [x] PASS, FAIL, UNKNOWN, INVALID, UNSUPPORTED, and implementation-error paths are
  distinct.
- [x] Agreement/unsupported/disagreement summary is machine-readable.
- [ ] Independent operator reproduction: **OPEN**.
- [ ] Organizational independence evidence: **OPEN**.

## Security, privacy, and migration

- [x] Internal adversarial review and regression coverage.
- [x] Historical claim preservation and exact dispatch.
- [x] No automatic upgrade; missing facts remain UNKNOWN.
- [ ] External security/privacy acceptance: **OPEN**.
- [ ] Independent compatibility review: **OPEN**.

## Release authorization

- [x] Implementation, evidence, review, governance, and authorization readiness are
  separate.
- [x] Known limitations, external review request, release-notes template, and evidence
  index exist.
- [ ] Active maintainer/editor roster: **OPEN**.
- [ ] Conflict disclosures and recusals: **OPEN**.
- [ ] Release authority: **OPEN**.
- [ ] Signing authority and protected key custody: **OPEN**.
- [ ] Final release authorization: **OPEN**.

No tag, signature, publication, merge, or release is authorized by this checklist.
