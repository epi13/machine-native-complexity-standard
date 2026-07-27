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
- Recomputed-block benefit versus LRU

The captured development run records a **12.844% reduction in recomputed blocks versus the
LRU baseline**, while the low-reuse control workload remains unchanged. Planning work also
stays within the preregistered limit.

## What it does not evaluate

CacheForge does not run a language model, allocate real GPU memory, connect to an inference
server, or establish production isolation. Its formal MNCS and MNCDS statuses remain
`UNKNOWN` pending protected holdout traces, independent evaluation, cross-host reproduction,
and a real serving-system adapter.

See the [executable CacheForge study](https://github.com/epi13/machine-native-complexity-standard/tree/main/case-studies/cacheforge)
for the contract, preregistration, threat model, generated candidate, tests, and checked-in
evidence.
