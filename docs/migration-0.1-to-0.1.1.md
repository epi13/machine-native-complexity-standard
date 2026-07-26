# Migrating schema 0.1 bundles to 0.1.1

Do not edit a historical 0.1 bundle in place when its identity matters. Copy it,
retain the old manifest as historical evidence, and create fresh 0.1.1 observations.

1. Change `schema_version` to `0.1.1` while keeping `mncs_version` at `0.1`.
2. Index the readable contract explicitly and give every evidence object a unique
   stable ID.
3. Replace status-valued acceptance-policy fields with `required_gates`,
   UNKNOWN/conflict policy, objective semantics, thresholds, sample requirements,
   and regression policy.
4. Replace path-valued gate references with evidence-index IDs in `gate_results`.
5. Create content-addressed generator, evaluator, environment, toolchain, harness,
   corpus, and build identities as applicable.
6. Bind every result to the contract and exact candidate source hash. Bind the
   reference hash when comparison is involved.
7. Supply only the cumulative artifacts required by the claimed level. L1 does not
   need placeholder L4 or L5 evidence.
8. Recompute every file and index hash, then run `mncs validate --require-pass`.
9. Use `mncs certify` only after the report is valid and computed PASS.

Legacy 0.1 files remain readable and validate against frozen schemas. They report
`legacy_self_asserted_acceptance: true`. Certification refuses them unless
`--allow-legacy` is explicit, and the override remains reduced-assurance.

See `examples/minimal` for the smallest evidence-derived form and
`examples/legacy-0.1` for the compatibility form.
