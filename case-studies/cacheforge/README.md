# CacheForge LLM KV-cache case study

CacheForge is a bounded, trace-driven MNCS research case study for an AI/ML
infrastructure component: LLM key-value cache allocation, prefix reuse, and eviction.
It compares a readable FIFO reference, a conventional LRU baseline, and a generated
64-state eviction table under the same deterministic hybrid-cache simulator.

The machine-generated policy can only propose victims. A compact readable authority
validates that every proposed block exists, is unique, has no live owners, and can be
evicted without exceeding the declared memory envelope. Invalid proposals are rejected
and routed through a readable LRU fallback before state mutation.

## Captured development result

The checked-in development study passes its declared gates:

- **12.844% fewer recomputed blocks than LRU** across the declared traces;
- no recomputation regression in the low-reuse control workload;
- deterministic planning work below the declared 1.50 baseline ratio;
- duplicate and unknown-victim mutation policies rejected without corruption;
- checkpointed and uninterrupted execution converge on the same final state digest.

This is not a production inference-serving claim. Formal MNCS and MNCDS status remain
`UNKNOWN`. The study does not execute a model, allocate GPU memory, connect to vLLM, or
demonstrate production tenant isolation.

## Architecture

```text
model cache groups + request trace
                |
                v
      generated eviction table
           proposal only
                |
                v
      readable allocation authority
       validate / reject / fallback
                |
                v
 deterministic hybrid-cache simulator
                |
       +--------+---------+
       |                  |
       v                  v
 evidence metrics     checkpoint digest
```

The simulator includes one full-attention cache group and one sliding-window group. It
models exact prefix identities, request ownership, cancellation, block pressure, eviction,
checkpoint restore, and deterministic final-state hashing.

## Run

From the repository root:

```bash
make cacheforge-test
make cacheforge-study
```

Or from this directory:

```bash
make test
make study
```

`make study` verifies the generated candidate, runs the test suite, evaluates all declared
scenarios and policies, executes mutation and recovery checks, and rewrites
`evidence/results/study-summary.json` deterministically.

## Repository layout

```text
contract/                 readable scope, authority, and invariant contract
generator/                frozen generated-policy specification
machine/                  generated 64-state eviction table
src/cacheforge/           simulator, authority, policies, scenarios, and evaluator
tests/                    invariant, mutation, recovery, and selection tests
tools/                    deterministic generator and controlled study runner
evidence/results/         checked-in development observations
preregistration.json      frozen thresholds and selection rule
threat-model.json         threats, mitigations, and residual UNKNOWNs
assurance-case.json       bounded development assurance record
```

## Claim boundary

A development `PASS` means only that the selected candidate passed the declared deterministic
simulator protocol in the captured environment. It does not establish GPU correctness,
production performance, protected-holdout independence, inference-server compatibility,
or formal MNCS/MNCDS conformance.
