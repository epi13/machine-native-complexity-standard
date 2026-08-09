# Execution assurance for MNCS and MNCDS test evidence

MNCS and MNCDS now have an experimental companion record for separating **what a test
reported** from **how much confidence the execution environment justifies**.

The implementation is deliberately offline. It validates identities, status relationships,
challenge freshness, declared isolation properties, attestation class, and custody claims. It does
not launch tests, providers, containers, virtual machines, or privileged sandbox helpers.

This distinction prevents a test result from silently inheriting stronger authority than the
execution environment actually established:

```text
subject result PASS + execution assurance UNKNOWN = combined UNKNOWN
subject result PASS + execution assurance PASS    = combined PASS
any required FAIL                                 = combined FAIL
```

The normal `FAIL > UNKNOWN > PASS` lattice is retained. MNCS and MNCDS results remain separate.

## Runner receipt linkage

The experimental `mncs-execution-receipt` profile is the observation layer beneath
this assurance record. A runner emits the immutable receipt with the effective
subject, bundle, policy, runner, environment, challenge, lifecycle, result, output,
resource, and raw enforcement facts. An assurance record may reference that receipt
through `execution_receipt`; the binding checker then compares those facts and fails
closed on substitution or an assurance property that the receipt reports as
`not-enforced` or `unknown`.

Receipt validation does not create assurance. A completed process or harness `PASS`
does not establish filesystem isolation, sandboxing, host-root resistance, protected
custody, independent operation, MNCS/MNCDS conformance, or promotion. Placement
remains a separate optional evidence reference. See
[experimental typed execution receipts](execution-receipts.md).

## Companion record

The experimental `mncs-execution-assurance` record binds:

- the MNCS or MNCDS subject family and record kind;
- the subject record's RFC 8785 canonical SHA-256 identity;
- the candidate identity where applicable;
- the reported test status and result identity;
- the test-bundle and execution-policy identities;
- runner and environment identities;
- a fresh challenge nonce and validity window;
- explicit execution properties;
- the attestation class, signer, verification state, and freshness; and
- limitations and the assurance properties required for the claim.

The schema is available as `schemas/mncs-execution-assurance-0.1.schema.json` and as the packaged
schema name `execution-assurance-0.1`.

## Execution properties

The record does not use one ambiguous `sandboxed` flag. It records each property independently:

| Property | Meaning |
| --- | --- |
| `command_bound` | The executed command was bound to the declared policy. |
| `environment_bound` | Material environment inputs were identified and constrained. |
| `filesystem_isolation` | The candidate could access only the declared filesystem surfaces. |
| `network_isolation` | Network access matched the declared policy. |
| `process_isolation` | Process creation and process-tree behavior were constrained. |
| `resource_limits` | CPU, memory, process, time, and output bounds were enforced as declared. |
| `test_integrity` | The test bundle used by the run matched its bound identity. |
| `result_integrity` | The reported result matched the bound execution output. |
| `host_root_resistance` | Host root could not silently manufacture an accepted result. |
| `protected_custody` | Protected tests or evidence remained under the declared custody. |
| `independent_operation` | The evaluator was operated by a legitimately separate authority. |

Only properties listed in `required_properties` participate in the base assurance result, but all
properties remain visible so weaker claims cannot be mistaken for stronger ones.

## Attestation classes

The reference validator recognizes these classes:

- `none` — no verified execution attestation;
- `local-record` — local execution metadata without a separate signature boundary;
- `signed-local` — locally controlled signed execution evidence;
- `platform-quote` — a measured-platform quote such as TPM-backed evidence;
- `confidential-vm` — a confidential guest measurement and attestation; and
- `external-evaluator` — an attestation from a separately controlled evaluator.

A local record or local signature cannot establish host-root resistance, protected custody, or
organizational independence. A platform quote or confidential VM does not by itself create
protected custody or organizational independence. Those overclaims fail closed.

## Commands

Validate an MNCS record together with its execution-assurance companion:

```bash
mncs-test-evidence validate measurement \
  examples/release-candidate-0.3/measurement-profile.json \
  execution-assurance.json \
  --at 2026-07-28T12:00:00Z \
  --require-pass --json
```

Validate an MNCDS development record under the same rules:

```bash
mncds-test-evidence validate \
  examples/mncds-0.1-rc/development-record.json \
  execution-assurance.json \
  --at 2026-07-28T12:00:00Z \
  --require-pass --json
```

Validate only the companion record:

```bash
mncs-test-evidence validate-assurance execution-assurance.json \
  --subject measurement-profile.json --kind measurement --json

mncds-test-evidence validate-assurance execution-assurance.json \
  --subject development-record.json --json
```

Exit codes follow the existing validator convention:

- `0` — valid; a non-PASS result is allowed unless `--require-pass` was requested;
- `1` — invalid record or binding;
- `2` — operational input error;
- `3` — valid but not combined PASS when PASS was required; and
- `4` — unsupported schema version.

## Host-root boundary

No ordinary process sandbox can make hostile host root disappear. Namespaces, seccomp, Landlock,
cgroups, containers, microVMs, and read-only mounts can strongly constrain the candidate while the
host kernel remains trusted.

The stronger target is therefore:

> Host root may deny service, but cannot produce a verifier-accepted false PASS without violating
> a measured identity, fresh challenge, cryptographic attestation, or external custody boundary.

Achieving that target requires later runner, TPM, confidential-computing, or external-evaluator
work. The current implementation validates those claims when evidence is supplied; it does not
manufacture them.

See [Execution-assurance implementation next steps](execution-assurance-next-steps.md). The
normative proposal is tracked as RFC 0008 under the repository's `rfcs/` directory.
