# FAQ

## Is complexity rewarded?

No. It is a cost that must be justified by a predeclared benefit.

## Does MNCS require AI-generated code?

No. It applies to machine-generated or machine-optimized artifacts regardless of the
generator technique.

## Does MNCS require a specific analyzer?

No. MNCS describes evidence capabilities and boundaries without privileging a specific
structural provider. Forge can discover explicitly configured providers, but neither
Forge nor source reading substitutes for an unavailable capability.

## Is L5 proof that software is safe?

No. It is a stronger, bounded evidence and lifecycle claim, not a warranty.

## Can UNKNOWN pass after manual review?

The provider result remains UNKNOWN. Review may reject it or add new evidence under
the declared policy; it cannot silently relabel uncertainty.

## Why can a rejected bundle validate?

Validation checks truthfulness and consistency. A faithfully recorded FAIL is valid
evidence of rejection.

## Is a validator PASS accredited certification?

No. MNCS 0.2 remains experimental. PASS is limited to the indexed contract,
candidate, evidence, and environment.

## Can I still validate a schema 0.1 bundle?

Yes. It uses frozen legacy schemas and reports self-asserted acceptance. Certification
requires an explicit `--allow-legacy` override and still reports reduced assurance.

## Why are content hashes not enough?

A hash identifies bytes, not whether those bytes concern this candidate, were
produced by the claimed evaluator, or correctly derive a threshold. Schema 0.1.1
also checks identity records and semantic bindings.
