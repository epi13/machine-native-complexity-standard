# RFC 0008: Execution assurance for MNCS and MNCDS test evidence

Status: Draft

This RFC proposes a shared companion record for distinguishing a functional test result from the
integrity, isolation, attestation, and custody of the environment that produced it. The draft
implementation does not change MNCS 0.2, MNCS 0.3-rc.1, or MNCDS 0.1-rc.1 normative schemas.

## Problem

A test can report PASS while an authorized process, ambient host permissions, mutable test files,
replayable output, or hostile host root can alter the test or result. A local hash-linked ledger can
detect later rewriting of retained records, but it does not prove that the test used at execution
was protected or that the host administrator could not manufacture an accepted result.

No ordinary process or container sandbox eliminates hostile host root. Stronger claims require a
measured platform, confidential guest, external key release, or separately controlled evaluator.

## Proposal

Add an experimental `mncs-execution-assurance` companion record that binds:

- the canonical identity and family of the MNCS or MNCDS subject record;
- candidate and test-result identities;
- test-bundle, policy, runner, and environment identities;
- a fresh verifier challenge;
- independently stated command, environment, filesystem, network, process, resource, test-integrity,
  result-integrity, host-root, custody, and independence properties; and
- an attestation class and verification state.

The companion record has its own assurance result. The combined test-evidence result uses the
existing lattice:

```text
combined = aggregate(subject test status, execution assurance status)
FAIL > UNKNOWN > PASS
```

A functional PASS with missing or unsupported execution assurance therefore remains UNKNOWN when
combined PASS is required.

## Attestation interpretation

The reference implementation recognizes local records, local signatures, platform quotes,
confidential VMs, and external evaluators without treating those classes as interchangeable.

- Local records and signatures cannot establish host-root resistance, protected custody, or
  organizational independence.
- A platform quote can support a bounded measured-host claim but does not by itself establish
  protected custody or organizational independence.
- A confidential VM can support a bounded hostile-host claim but does not by itself establish
  organizational independence.
- External evaluator status requires actual separate operation and custody; a second machine under
  the same operator is insufficient.

Contradictory claims fail closed. Missing evidence remains UNKNOWN.

## Compatibility

The companion format is additive and experimental. Existing records remain valid under their
historical semantics. The Python validator adds separate `mncs-test-evidence` and
`mncds-test-evidence` entry points rather than changing frozen release-candidate record shapes.

Ordinary offline validators continue not to execute tests, providers, candidates, containers, or
sandbox helpers. Execution backends produce evidence; validators interpret supplied evidence.

## Security boundary

The initial implementation validates declarations, identities, freshness, and claim consistency.
It is not an OS or network sandbox. Namespace, seccomp, Landlock, cgroup, verity, TPM,
confidential-computing, and external-custody work remains separate and must report unsupported
properties as UNKNOWN.

The intended strong-host objective is limited:

> Host root may deny service, but cannot produce a verifier-accepted false PASS without violating
> a measured identity, fresh challenge, cryptographic attestation, or external custody boundary.

## Required evidence before acceptance

Before this RFC can be accepted as normative, the project requires:

- stable schema and migration review;
- adversarial subject, test, policy, runner, result, and replay fixtures;
- an implemented isolation runner with explicit capability reporting;
- Python and independent Rust agreement over a bounded corpus;
- a reviewed threat model for local, measured-host, confidential-VM, and external-evaluator modes;
- external security and privacy review;
- explicit future claim-level requirements; and
- governance approval that identifies the normative version and compatibility rules.

The ordered development work is recorded in
[`docs/execution-assurance-next-steps.md`](../docs/execution-assurance-next-steps.md).
