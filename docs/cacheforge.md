# CacheForge LLM KV-cache case study

CacheForge applies the machine-native complexity model to an AI/ML infrastructure problem:
LLM KV-cache allocation, prefix reuse, and eviction under bounded memory pressure.

The study deliberately separates optimization from authority. A generated 64-state table
ranks evictable cache blocks, but it cannot mutate state. A readable authority verifies
block identity, uniqueness, liveness, capacity, and fallback safety before any eviction.

## What the study evaluates

- Full-attention and sliding-window cache groups
- Exact prefix-key reuse
- Request completion and cancellation
- Bounded block pressure and eviction
- Generated-policy identity and deterministic regeneration
- Invalid planner proposals
- Checkpoint continuity
- Recomputed-block benefit versus conventional policies
- Seeded workload distributions across multiple cache capacities
- External trace-bundle validation without automatic claim promotion

## Initial development result

The initial development run records a **12.844% reduction in recomputed blocks versus LRU**,
while the low-reuse control remains unchanged. That benefit is concentrated in the
alternating-tenant workload, so the result is intentionally bounded rather than presented
as general KV-cache superiority.

## Evaluation epoch 2

Epoch 2 evaluates 16 paired seeds across capacities of 16, 24, 32, and 48 blocks. The 64
scenarios contain 3,072 requests and compare the frozen candidate against both LRU and
segmented LRU, using the stronger conventional result for each scenario.

The candidate records 39,654 recomputed blocks versus 41,167 for the strongest baselines,
a **3.675% aggregate reduction**. It improves 53 of 64 scenarios, with a median ratio of
0.966886, p95 ratio of 1.035928, and worst ratio of 1.051546.

The broader protocol also reveals a weakness: at 48 blocks the candidate regresses in 9 of
16 scenarios, although its aggregate at that capacity remains slightly favorable. Epoch 2
therefore remains `REVIEW_REQUIRED`, with formal MNCS and MNCDS status `UNKNOWN`.

## Protected evaluation boundary

An external evaluator accepts bundles conforming to the checked-in trace schema, records
the exact input digest, and compares the frozen candidate with both conventional baselines.
It cannot promote a formal claim: every result retains `UNKNOWN`, requires review, and sets
`promotion_authorized` to `false`.

Protected traces themselves are not included in the repository. Independent custody,
protected-holdout integrity, and release review remain external obligations.

## What it does not evaluate

CacheForge does not run a language model, allocate real GPU memory, connect to an inference
server, or establish production isolation. Protected traces, independent evaluator custody,
cross-host reproduction, and a real serving-system adapter remain outstanding.

See the [executable CacheForge study](https://github.com/epi13/machine-native-complexity-standard/tree/main/case-studies/cacheforge)
for the contract, preregistrations, generated candidate, tests, external bundle schema, and
checked-in evidence.
