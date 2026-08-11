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
- Strict external trace-bundle validation without automatic claim promotion

## Initial development result

The initial development run records a **12.844% reduction in recomputed blocks versus LRU**,
while the low-reuse control remains unchanged. That benefit is concentrated in the
alternating-tenant workload, so the result is intentionally bounded rather than presented
as general KV-cache superiority.

## Evaluation epoch 2

Epoch 2 evaluates 16 independent seeded traces at capacities of 16, 24, 32, and 48 blocks.
The resulting 64 paired evaluations contain 3,072 requests and compare the frozen candidate
against both LRU and segmented LRU, using the stronger conventional result for each case.

The candidate records 39,654 recomputed blocks versus 41,167 for the strongest baselines,
a **3.675% aggregate reduction**. It improves 53 of 64 evaluations, with a median ratio of
0.966886, p95 ratio of 1.035928, and worst ratio of 1.051546.

The broader protocol also reveals a meaningful regime limitation. At 48 blocks the
candidate regresses in 9 of 16 evaluations, although its aggregate at that capacity remains
slightly favorable. Those high-capacity regressions cluster when the workload contains only
one or two hot system-prefix families. Epoch 2 therefore remains `REVIEW_REQUIRED`, with
formal MNCS and MNCDS status `UNKNOWN`.

## Evidence integrity amendment

A post-run review improved evidence integrity without changing the candidate, workload, or
performance gates:

- every scenario-level observation is published in a deterministic evidence record;
- the summary binds the candidate, generator, simulator, authority, baselines, evaluator,
  protocol, and schema by SHA-256;
- seed-clustered and hot-prefix-regime summaries are emitted alongside capacity summaries;
- the external loader validates bundles against the published JSON Schema before parsing.

## Protected evaluation boundary

An external evaluator accepts schema-valid bundles, records the exact input digest, and
compares the frozen candidate with both conventional baselines. It reports schema validity
separately from protocol eligibility and custody verification. A schema-valid bundle does
not by itself establish protected-protocol eligibility or independent custody.

The evaluator cannot promote a formal claim: every result retains `UNKNOWN`, requires
review, and sets `promotion_authorized` to `false`.

Protected traces themselves are not included in the repository. Independent custody,
protected-holdout integrity, and release review remain external obligations.

## What it does not evaluate

CacheForge does not run a language model, allocate real GPU memory, connect to an inference
server, model continuous batching, or establish production isolation. Protected traces,
independent evaluator custody, cross-host reproduction, and a real serving-system adapter
remain outstanding.

See the [executable CacheForge study](https://github.com/epi13/mncs-reference-studies/tree/main/case-studies/cacheforge)
for the contract, preregistrations, generated candidate, tests, external bundle schema,
identity-bound summary, and complete scenario evidence.
