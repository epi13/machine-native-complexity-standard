# Experimental execution-placement evidence

The `execution-placement-evidence` profile is an experimental, non-normative
description of how one bounded computation was placed and executed. It is a resource
and evidence vocabulary, not a scheduler, model runtime, correctness oracle, or
conformance profile.

Validate it with the public offline path:

```bash
mncs schema execution-placement --json
mncs validate-placement experimental/execution-placement/fixtures/valid/sequential-offload.json --json
```

## What the record binds

Each record binds subject, artifact/provider, executable/runtime, and environment
identities twice: the declared identity and the identity observed at execution. A
changed runtime or environment is stale evidence, not a silently reusable result. An
execution-assurance record, measurement identity, and experiment identity are optional
references; placement evidence does not subsume execution assurance.

The requested policy is separate from the observed placement:

| Requested policy | Possible observed placement |
| --- | --- |
| `cpu` | `cpu-only` |
| `accelerator` | `full-accelerator` |
| `sequential-offload` | `sequential-offload` |
| `auto` | CPU, full accelerator, sequential offload, or a bounded recovery result |

`capability_observations.discovered` means that a backend reported an available
accelerator. `execution_probe: PASS` means a runtime execution probe succeeded. The
former never implies the latter. A configuration value alone cannot prove offload.

Provider/process lifetime is independent of physical placement. A persistent provider
may keep its process alive while weights remain in host RAM and modules move
transiently to an accelerator. `residency.provider_lifetime` and
`residency.weight_placement` preserve that distinction.

Resource limits use explicit units and measurements identify metric, source, unit, and
phase. `cold-load` and `warm-execution` observations are not interchangeable. Missing
optional observations remain absent; a limit without a supporting observation yields
`UNKNOWN`. A value exactly equal to a hard cap is within that cap.

Only AUTO may use declared fallback transitions. A transition must be listed in the
record's allowed set, authorized, and terminate at the observed placement. Explicit
CPU, accelerator, and sequential-offload requests fail closed if execution silently
uses another strategy. A bounded OOM recovery such as
`full-accelerator -> sequential-offload -> cpu` records the transitions and cause; it
does not claim that recovery is universally safe or superior.

## Result separation and claim boundary

The record keeps four results separate:

1. execution succeeded or failed;
2. placement evidence is supported, unsupported, or unknown;
3. the declared resource policy was respected, violated, or unknown; and
4. the aggregate placement-profile status.

The aggregate uses `FAIL > UNKNOWN > PASS`. A narrow placement `PASS` means only that
the identified bounded execution completed and required placement evidence supported
the declared placement under the recorded policy. It does not establish algorithmic
or semantic correctness, model quality, numerical equivalence, MNCS/MNCDS
conformance, security, isolation, sandboxing, independence, protected custody,
causal superiority, general performance superiority, suitability on another machine,
promotion, or release authorization.

The schema makes `conformance_claim` and `independence_claim` explicitly
`not-asserted`. Governing MNCS/MNCDS results, when available, are references to
separate authority records and do not enter the placement aggregate.

## Project-family flow

```text
MNEL investigator/provider or future Fabric executor
                       |
                       v
       runtime observations and placement witnesses
                       |
                       v
             execution-placement record
               /          |          \
              v           v           v
           Forge     execution     measurements
        micro-verifiers assurance
               \          |          /
                v         v         v
               MNCS/MNCDS governed evidence
                       |
                       v
               RAVEL advisory learning
```

MNEL providers may propose or perform bounded placement but cannot self-certify it.
Forge may eventually host a small verifier that checks whether runtime observations
support the declared placement, but Forge remains a development control plane and
does not duplicate this validator. RAVEL may retain raw observations, failures,
negative experience, and scoped causal hypotheses; it may not turn learned experience
or repeated local success into `PASS`, conformance, independence, or promotion.

The generic fixtures are inspired by constrained local vision providers and learned
micro-providers without making GIMP, MNEL, CUDA, or any particular machine normative.
CUDA is one possible backend detail, not a schema requirement.

## Follow-on research

Future work may add remote/Fabric executor bindings, heterogeneous CPU/GPU/NPU
placement, deterministic placement comparisons, a bounded Forge placement verifier,
energy/power observations, distributed execution, or provider isolation evidence.
Those are separate research tasks and are not implied by this profile.
