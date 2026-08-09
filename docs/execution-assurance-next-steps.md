# Execution-assurance implementation next steps

This is the ordered Codex handoff for turning the companion execution-assurance record into
increasingly strong, evidence-backed MNCS and MNCDS test execution. It is not authorization to
claim that the current repository implements a sandbox, host-root resistance, protected custody,
or independent evaluation.

Each task should normally be a separate focused pull request. Preserve frozen MNCS 0.2 and release-
candidate semantics unless an approved RFC explicitly changes them.

## Invariants for every task

- Keep functional test status separate from execution assurance.
- Apply `FAIL > UNKNOWN > PASS` without inferring missing evidence.
- Bind subject, candidate, test bundle, policy, runner, environment, challenge, output, and
  attestation identities.
- Do not let a skipped or unavailable isolation backend fall back to ordinary execution and PASS.
- Keep MNCS implementation results and MNCDS development-process results separate.
- Do not treat signatures, additional machines, or confidential hardware as organizational
  independence without the corresponding authority and custody facts.
- Ordinary offline validation must never launch a provider or candidate.

## Current implementation state — 2026-08-08

EA-NEXT-001 is implemented in this repository as the non-normative
`mncs-execution-receipt` `0.1-experimental` profile. The schema, canonical identity,
offline validator, CLI/API path, optional execution-placement linkage, assurance
binding checks, reference receipt, and adversarial corpus are present. The receipt
records observations and does not implement a sandbox, signed attestation, immutable
test bundle, custody, independent evaluation, conformance, or promotion. Historical
acceptance criteria below are retained; remaining EA-NEXT tasks are still open.

## EA-NEXT-001 — Add typed execution receipts

**Depends on:** this companion-record foundation

**Status: IMPLEMENTED in MNCS as `0.1-experimental`; this status does not imply
RFC approval or completion of any later assurance task.**

Define a typed runner receipt used by local workflows, Provider Protocol integrations, portable
host execution, and Forge adapters. The receipt must contain every identity represented by the
execution-assurance record and must be created by the runner rather than reconstructed from prose.

Acceptance criteria:

- receipts are immutable, versioned, and canonically hashable;
- status, stdout, stderr, retained output, timeout, crash, and output-limit outcomes remain
  distinct;
- the runner reports enforced and unenforced properties separately;
- incomplete receipts remain `UNKNOWN`; and
- subject substitution, policy substitution, and result substitution fixtures fail.

## EA-NEXT-002 — Build immutable test bundles

**Depends on:** EA-NEXT-001

Package tests, harnesses, expected manifests, runtime requirements, and policy references in a
content-addressed bundle. Bind every execution request to the bundle's canonical identity.

Acceptance criteria:

- path traversal, symlink, duplicate-path, case-collision, oversized-file, and archive-expansion
  attacks are rejected;
- changing any test or harness byte changes the bundle identity;
- mutable tags or branch names cannot serve as final identities;
- old successful results cannot be reused against a different bundle; and
- bundle verification remains offline.

## EA-NEXT-003 — Implement the Linux isolation runner

**Depends on:** EA-NEXT-001 and the stable runner interface

Implement an optional Linux runner using a new user, mount, PID, IPC, UTS, and network namespace;
read-only root, subject, and test mounts; a bounded writable `tmpfs`; `pivot_root`; `no_new_privs`;
seccomp; Landlock; cgroup v2; no inherited file descriptors; and process-tree cleanup.

Acceptance criteria:

- adversarial fixtures cannot modify tests, escape mounts, access undeclared files, use the
  network, create unbounded processes, exceed resource limits, or retain children;
- every unavailable kernel feature is recorded explicitly;
- requested properties that cannot be enforced remain `UNKNOWN` rather than falling back;
- the runner never accepts caller-controlled shell text, executable paths, environment, or working
  directories; and
- hostile host root remains documented as trusted at this level.

## EA-NEXT-004 — Add verity-enforced test integrity

**Depends on:** EA-NEXT-002 and EA-NEXT-003

Add an optional backend for `fs-verity` or an equivalent measured read-only content mechanism.
Record whether integrity was merely hashed before execution or enforced during file access.

Acceptance criteria:

- test replacement after request creation is detected;
- corruption during access fails the run;
- the authorized digest is bound to the policy and receipt;
- unsupported filesystems remain `UNKNOWN`; and
- verity enforcement is not mislabeled as external custody.

## EA-NEXT-005 — Add challenge issuance and replay tracking

**Depends on:** EA-NEXT-001

Introduce a verifier-issued cryptographic nonce with an explicit validity window and a local or
external replay store. Bind the nonce into every signed or quoted execution result.

Acceptance criteria:

- stale, duplicated, missing, and mismatched challenges fail;
- wall-clock rollback alone cannot make an expired result current;
- restart and interrupted-write behavior are tested;
- a challenge cannot be reused across subject, bundle, policy, or runner identities; and
- offline verification can consume a supplied replay receipt without contacting a service.

## EA-NEXT-006 — Sign and verify execution attestations

**Depends on:** EA-NEXT-001 and EA-NEXT-005

Use the existing canonicalization, DSSE/Ed25519, trust-policy, expiration, and revocation machinery
to sign execution receipts. Keep cryptographic validity separate from authority and custody.

Acceptance criteria:

- tampering with any material identity invalidates the signature;
- revoked, expired, untrusted, or insufficient-role signatures do not produce assurance PASS;
- self-signed local evidence remains locally controlled;
- multi-signature thresholds are deterministic and offline; and
- both Python and the independent Rust consumer agree on the bounded format before it is added to
  the shared release-candidate corpus.

## EA-NEXT-007 — Add TPM measured-platform attestation

**Depends on:** EA-NEXT-005 and EA-NEXT-006

Verify a fresh TPM quote and event log against an approved boot, kernel, launcher, policy, and
runner measurement set. Bind the challenge and execution receipt to the quote.

Acceptance criteria:

- mismatched PCR values, event logs, nonces, policies, and runner identities fail;
- approved measurement sets are versioned and explicit;
- host-root resistance is claimed only within the measured-boot threat model;
- denial of service remains possible and documented; and
- TPM evidence alone does not create protected custody or organizational independence.

## EA-NEXT-008 — Add confidential-VM evaluation

**Depends on:** EA-NEXT-002, EA-NEXT-005, and EA-NEXT-006

Implement a confidential-VM backend such as SEV-SNP or TDX with measured guest boot, immutable
bundle delivery, remote attestation, and optional key release after measurement verification.

Acceptance criteria:

- the verifier checks the guest measurement and fresh challenge before accepting a result;
- protected test material is released only to an approved guest measurement when key release is
  enabled;
- debug or migration modes that weaken confidentiality are rejected or explicit `UNKNOWN`;
- host-controlled result substitution fails; and
- confidential execution alone is not called organizational independence.

## EA-NEXT-009 — Add external evaluator custody

**Depends on:** stable signed receipts and bundle identities

Create a portable evaluation kit for a separately controlled operator. The external evaluator must
control its signing key, challenge issuance, test custody, execution, and release of the final
receipt.

Acceptance criteria:

- local project users cannot forge the evaluator signature;
- the custody and operator relationship are explicit records rather than inferred from machine
  count;
- same-operator remote hosts remain same-operator evidence;
- protected holdout access and disclosure are auditable; and
- external independence remains `UNKNOWN` until a legitimate actor accepts and performs the role.

## EA-NEXT-010 — Integrate MNCS and MNCDS case studies

**Depends on:** EA-NEXT-001 through the runner level being evaluated

Apply companion execution assurance to the recursive analyzer study, RAVEL, portable host cohorts,
release-candidate checks, and selected language/provider evidence. Do not rewrite historical
records.

Acceptance criteria:

- new epochs link to old evidence without relabeling it;
- each study preregisters required assurance properties;
- ordinary local runs demonstrate the expected `PASS + UNKNOWN = UNKNOWN` behavior;
- adversarial runs cover test overwrite, runner substitution, policy drift, replay, output
  substitution, and host-root limitations; and
- case-study claims state exactly which assurance level was observed.

## EA-NEXT-011 — Add independent Rust validation and corpus vectors

**Depends on:** schema and semantic review plus stable format

Implement the same bounded execution-assurance decisions in the independent Rust consumer and add
positive and negative vectors to a separate experimental corpus before considering inclusion in the
shared release-candidate corpus.

Acceptance criteria:

- Python and Rust agree on every vector;
- vectors cover all attestation classes, dynamic freshness, status mismatch, identity mismatch,
  and authority overclaim;
- unsupported future versions remain `UNKNOWN`/unsupported rather than guessed;
- corpus count and release metadata remain synchronized; and
- agreement is not mislabeled as independent operation of the evaluator.

## EA-NEXT-012 — Resolve RFC and release integration

**Depends on:** implementation evidence and review

Review RFC 0008, determine whether execution assurance belongs in a future MNCS/MNCDS normative
revision, and define migration and compatibility rules. Codex may prepare the packet but cannot
approve it.

Acceptance criteria:

- normative and experimental fields are clearly separated;
- the required assurance properties for each future claim class are explicit;
- older records remain valid under their historical semantics;
- security, privacy, external review, dissent, and governance records are retained; and
- no release status changes without legitimate approval.
