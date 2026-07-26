# Machine-Native Complexity Development Specification

MNCDS is the experimental development-process companion to MNCS.

MNCS asks whether a selected implementation is supported by adequate correctness, safety,
resource, structural, performance, provenance, and regeneration evidence. MNCDS asks
whether the process that generated, compared, selected, released, and later replaces that
implementation remained controlled and auditable.

The two claims remain separate:

```text
MNCDS-D3 / MNCS-L4
```

The first result describes development-process assurance. The second describes candidate
implementation conformance. Neither implies the other.

## Profiles

| Profile | Required control surface |
|---|---|
| D1 | Charter, immutable baseline, bounded generator, candidate identities, lineage, ledger, explicit PASS/FAIL/UNKNOWN |
| D2 | Pinned environment, evidence partitions, reproducibility class, repeated measurement, evaluator regression corpus |
| D3 | Predeclared selection, protected holdout, independent final evaluator, role-conflict checks, MNCS binding |
| D4 | Release identity, monitoring thresholds, tested rollback, regeneration drill, retirement triggers |

Profiles are cumulative.

## Offline validation

Install the repository and validate the reference record:

```bash
python -m pip install -e '.[dev]'
mncds validate examples/mncds-d4/development-record.json --require-pass
```

Machine-readable output is available with `--json`. The validator performs schema and
cross-record semantic checks. It never launches or imports a generator, candidate,
evaluator, analyzer, benchmark, or evidence binary.

The experimental validator currently checks:

- required roles and role uniqueness;
- forbidden generator authority;
- evidence-partition identity overlap and holdout contamination;
- candidate identity uniqueness, parent existence, and lineage cycles;
- selected-candidate presence and disposition;
- required FAIL and UNKNOWN treatment;
- cumulative D2 reproducibility requirements;
- D3 holdout, predeclared-selection, authority, executable, and evidence independence;
- candidate/contract/environment agreement with an MNCS binding;
- D4 rollback and regeneration-drill outcomes.

## Recursive improvement

Evidence from epoch `n` may improve a Joern harness, evaluator, generator, or search
strategy in epoch `n+1`. The changed toolchain receives a new identity, preserves the
failure cases that motivated the update, reruns its regression corpus, and must not reuse
a contaminated protected holdout for the same acceptance claim.

## Status

MNCDS 0.1 remains a draft under RFC 0004. The validator and schemas are experimental
implementations intended to make the proposal testable during review. They do not make
the draft an accredited or accepted external standard.
