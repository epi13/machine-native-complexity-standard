# Experimental typed execution receipts

`mncs-execution-receipt` `0.1-experimental` is a runner-produced, immutable
observation envelope. It records what a bounded runner actually observed; it is
not a correctness result, MNCS/MNCDS conformance result, assurance verdict,
sandbox claim, custody record, independence claim, certification, or promotion.

## Identity and binding

The receipt binds a subject and candidate, test bundle and input snapshot, policy
and requested limits, effective runner and command identities, environment, and
the exact execution-assurance challenge. `receipt_identity` is the lowercase
canonical SHA-256 of the complete receipt with only `receipt_identity` removed.
The record is deterministic for the same frozen observations and any material
change requires a new identity.

The envelope keeps runner lifecycle, process termination, harness status, result
artifact identity, output retention, resource measurements, and enforcement facts
separate. A completed process with harness `PASS` is not automatically an
execution-assurance `PASS`. A timeout, crash, nonzero exit, or output-limit event
is a valid observation of an unsuccessful execution, not a malformed receipt.

`enforced`, `not-enforced`, and `unknown` are raw runner facts. Ordinary local
runners cannot use this profile to establish filesystem isolation, host-root
resistance, protected custody, organizational independence, security, or
conformance. The fixed claim boundary in every receipt makes those limits
machine-readable.

## Placement relationship

The receipt optionally references an execution-placement record by record ID,
canonical identity, subject identity, and environment identity. It does not copy
that profile. Placement evidence can describe CPU-only, full accelerator,
sequential offload, probes, residency, fallback, and resource observations while
remaining separate from execution assurance. A receipt validator can resolve and
check the reference when the placement record is supplied; an unresolved
reference remains `UNKNOWN`.

## Immutable bundle relationship

EA-NEXT-002 provides the [experimental immutable execution bundle](execution-bundles.md)
that the receipt's `bundle.test_bundle_identity` can bind to. Supplying `--bundle`
to receipt validation verifies the archive first, then compares its logical bundle,
harness, input, and policy identities with the receipt. The receipt does not need
to embed raw test material, and bundle verification does not prove that a runner
actually used the bundle; those are separate observation and assurance questions.

## Assurance relationship

An existing execution-assurance record may add an `execution_receipt` reference.
The binding checker compares subject, candidate, bundle, policy, runner,
environment, challenge, harness result, result identity, and enforcement facts.
Mismatches fail closed. Missing receipt evidence never creates assurance.

```text
request -> runner -> immutable receipt
                    |             |
                    v             v
              placement       assurance
                    \             /
                     governed evidence
```

The combined CLI remains backward compatible:

```bash
mncs schema execution-receipt --json
mncs validate-execution-receipt receipt.json --json
mncs validate-execution-receipt receipt.json --placement placement.json --require-pass
mncs-test-evidence validate-assurance execution-assurance.json \
  --receipt receipt.json --at 2026-08-08T00:30:00Z --json
```

## Project-family adapters

- Forge can populate lifecycle, timeout/crash, bounded stdout/stderr, resource
  outcomes, and policy/runner/environment identities from its hardened local
  process runner.
- MNEL can populate provider/runtime and snapshot identities, lifecycle, the
  placement-record reference, and accelerator/resource observations.
- GIMP Local MCP can populate actual device probes, sequential-offload evidence,
  OOM recovery, and observed allocation/RSS facts without making CUDA normative.
- A future Fabric executor can emit the same receipt before any attestation or
  custody layer is applied.
- RAVEL may retain receipt identities in episodes and causal attribution as
  immutable observations, but cannot edit or promote them.
- MNCS Commons and MNCS Language may supply compatible identities in future; this
 profile does not depend on either implementation.

## Challenge and replay relationship

EA-NEXT-005 now supplies the verifier-issued challenge and explicit local replay layer
around the receipt's existing `challenge.nonce`, `issued_at`, and `expires_at` fields.
The challenge binds those observations to the subject, candidate, bundle, policy, and
optional runner constraint before execution. `ReplayStore.consume` is the only mutating
operation; it emits an offline `mncs-replay-receipt` after one successful consumption.
Validation and replay verification remain non-mutating.

The replay receipt proves only internally consistent, single-use consumption in the
declared local store. A persisted watermark prevents a wall-clock rollback from making
an observed expired result current, but a host administrator can still replace the
store. Freshness does not establish isolation, correctness, custody, independence,
conformance, or promotion. See [execution challenges and replay](execution-challenges.md).

EA-NEXT-001 remains the typed receipt layer. EA-NEXT-002 is now implemented as the
immutable bundle layer. EA-NEXT-005 is implemented as the freshness layer. Linux isolation,
signed attestations,
measured platforms, and external custody remain later work and remain `UNKNOWN`
when not supplied.
