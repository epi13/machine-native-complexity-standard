# Machine-Native Evidence Analyzer

The Machine-Native Evidence Analyzer (MNEA) is an experimental reference architecture for
producing bounded evidence. It is not a normative dependency and is not a claim that one
analyzer can prove arbitrary program correctness.

## Purpose

MNEA evaluates declared structural, behavioral, safety, resource, and implementation
invariants and emits reproducible PASS, FAIL, or UNKNOWN evidence.

The architecture is deliberately focused on declared bounded claims rather than universal
whole-program analysis:

```text
source or artifact
    -> compiler-backed extractor
    -> normalized facts or evidence graph
    -> declarative invariant evaluator
    -> optional runtime and differential providers
    -> evidence reconciler
    -> MNCS-compatible evidence result
```

Ordinary MNCS validation remains offline. Provider execution is explicit and separate.

## Initial C provider

`experimental/mnea/clang_provider.py` is the first bounded prototype. It:

- accepts Provider Protocol 0.1 requests;
- analyzes one C11 source file at a time;
- invokes Clang AST JSON without a shell;
- caps source bytes and wall time;
- extracts direct functions, direct calls, unresolved calls, global variables, and inline
  assembly;
- evaluates a small declarative invariant set; and
- returns PASS, FAIL, or UNKNOWN with compact witnesses and limitations.

Supported experimental invariant kinds are:

- `forbidden_calls`;
- `required_calls`;
- `no_recursion`;
- `no_mutable_globals`;
- `no_inline_assembly`; and
- `max_call_depth`.

Unknown invariant kinds, unavailable Clang, parse failure, unresolved calls relevant to a
claim, external mutable globals, and exceeded bounds remain UNKNOWN.

The provider does not claim sound alias analysis, macro semantics, whole-program linkage,
function-pointer resolution, compiler correctness, filesystem isolation, or network
isolation.

## Request shape

An analysis request uses Provider Protocol 0.1 and the analysis name
`c-structural-invariants`.

```json
{
  "protocol_version": "0.1",
  "type": "analysis_request",
  "request_id": "request-1",
  "analysis": "c-structural-invariants",
  "component": {
    "source_path": "candidate.c",
    "contract_id": "contract-http-decoder-v1",
    "mode": "evaluator",
    "evidence_partition": "holdout-1",
    "invariants": [
      {"id": "no-unsafe-copy", "kind": "forbidden_calls", "calls": ["strcpy"]},
      {"id": "no-recursion", "kind": "no_recursion"},
      {"id": "no-global-state", "kind": "no_mutable_globals"}
    ]
  },
  "limits": {
    "max_source_bytes": 1000000,
    "max_wall_seconds": 10
  },
  "extensions": {}
}
```

A production evaluator should bind the request, provider executable, configuration,
compiler, environment, source, contract, and invariants by stable identity before final
use.

## Evidence semantics

Each invariant produces its own result. Overall aggregation follows MNCS dominance:

1. any FAIL produces overall FAIL;
2. otherwise any UNKNOWN produces overall UNKNOWN;
3. otherwise all required results must PASS.

A PASS identifies the bounded method and declares required semantics complete within that
method. A FAIL includes a witness or counterexample where practical. An UNKNOWN states
what prevented resolution.

Runtime evidence cannot silently broaden into structural proof. Static evidence cannot
silently broaden into behavioral proof. Conflicting required evidence remains visible and
is handled by policy rather than averaged away.

## Evaluator and repair-feedback modes

### Evaluator mode

Evaluator mode uses frozen candidate, contract, invariants, policy, limits, compiler,
configuration, and environment identities. It does not modify the candidate or thresholds
and does not expose protected holdout content to generation.

### Repair-feedback mode

Repair-feedback mode may provide source locations, compact counterexamples, and
machine-readable repair constraints using development evidence. It has no final
conformance authority and no protected-holdout access.

Using one executable for both modes is acceptable only when authority, configuration,
partition, and execution identities remain distinguishable.

## Analyzer self-validation

The analyzer needs a versioned corpus containing:

- known valid cases;
- known violations;
- unsupported constructs;
- parser failures;
- extractor crashes;
- timeouts and memory bounds;
- aliasing and indirect calls;
- macros and compiler extensions;
- mutation-generated defects;
- adversarial inputs;
- provider disagreements; and
- cases where a naive analyzer would incorrectly PASS.

The primary safety metric is incorrect PASS, not merely total coverage or a low UNKNOWN
rate. Report true positives, false positives, false negatives, incorrect PASS, UNKNOWN,
crashes, timeouts, runtime, peak memory, determinism, and diagnostic utility.

A truthful UNKNOWN is preferable to unsupported PASS.

## Two-epoch recursive-improvement study

### Epoch one: historical Joern baseline

Freeze and identify:

- Joern version, plugins, dependencies, and environment;
- queries and query configuration;
- corpus and expected outcomes;
- evaluation policy and limits;
- known false positives, false negatives, UNKNOWN, crashes, and timeouts; and
- machine-visible feedback and treatment/control prompts where applicable.

Do not silently improve epoch one after it is frozen.

### Epoch two: focused analyzer or harness

Give the new analyzer, extractor, configuration, corpus, invariants, harness, environment,
and epoch new identities. Predeclare improvement objectives such as lower incorrect PASS,
lower false negatives, better UNKNOWN classification, lower resource cost, greater
determinism, or better diagnostic utility.

Use development and selection evidence only as permitted by MNCDS. Reserve a fresh
protected holdout for final comparison.

### Comparison

Compare at least:

- known-defect detection;
- false positives and false negatives;
- incorrect PASS and UNKNOWN;
- crash and timeout rates;
- runtime and peak memory;
- determinism;
- diagnostic utility;
- reproducibility;
- implementation effort; and
- evidence-output quality.

Disagreements and blind spots become classified regression fixtures. Unresolved cases
remain UNKNOWN. The study should produce an MNCDS development record and an MNCS bundle
for any selected machine-native candidate.
