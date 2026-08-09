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

This iteration implements EA-NEXT-001 only. Immutable test bundles, Linux
isolation, replay stores, signed attestations, measured platforms, and external
custody remain later work and remain `UNKNOWN` when not supplied.
