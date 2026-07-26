# MNCDS test and evidence plan

RFC 0004 requires executable evidence before MNCDS can move from draft to accepted
normative status. This page tracks that evidence without treating implementation work as
proof that the proposal is already accepted.

## Acceptance matrix

| Required demonstration | Repository artifact | Current state |
|---|---|---|
| D1 multiple-candidate ledger | D4 reference record reduced to D1 in `tests/test_mncds.py` | Implemented |
| Reject generator evaluator/threshold mutation | Unit tests and deterministic corpus mutations | Implemented |
| Reject omitted or promoted UNKNOWN | Unit tests and `invalid/unknown-promoted` corpus case | Implemented |
| D2 reproducible generation and repeated measurement | Seeded profile test and D4 reference record | Implemented |
| D3 protected holdout and independent evaluator | D3 profile test and D4 reference record | Implemented |
| Recursive harness improvement across epochs | Normative epoch rules and reference record supersession fields | Partially implemented; full two-epoch Joern study required |
| D4 rollback, regeneration drill, retirement | D4 reference record and rejection tests | Implemented |
| Independent validator agreement | Versioned corpus format ready for another implementation | Not yet satisfied |

## Deterministic corpus

Run:

```bash
PYTHONPATH=src python scripts/run-mncds-corpus
```

The corpus starts from one valid cumulative D4 record and applies declared JSON Pointer
mutations. Every case states its expected validity, computed status, and required issue
codes. This lets another implementation consume the same vectors without copying Python
validator behavior.

Current corpus coverage includes:

- forbidden evaluator and threshold mutation;
- candidate-lineage cycles;
- UNKNOWN promotion;
- holdout contamination;
- post-hoc selection rules;
- evaluator authority and executable conflicts;
- mismatched MNCS candidate binding;
- untested rollback;
- failed regeneration drills.

## Required independent evidence

RFC 0004 must not be accepted solely because the reference Python validator agrees with
its own tests. Before acceptance, at least one independently implemented consumer should:

1. parse `mncds-conformance-corpus/corpus.json` without importing the Python validator;
2. apply the declared mutations;
3. produce normalized validity, status, and issue-class outcomes;
4. publish an agreement report including every disagreement and unsupported rule;
5. preserve unsupported behavior as UNKNOWN rather than PASS.

A Rust implementation is a natural candidate because MNCS already uses Rust for
cross-language interoperability, but the standard does not require Rust.

## Recursive Joern study

The remaining high-value demonstration should use the repository's Joern harness work:

1. freeze the original harness, corpus, and evaluation policy as epoch 1;
2. evaluate at least two competing implementation or analysis ideas;
3. convert discovered disagreements and blind spots into classified regression fixtures;
4. create a newly identified epoch-2 harness;
5. rerun the harness regression corpus;
6. evaluate new candidates using a fresh protected holdout;
7. compare detection quality, UNKNOWN rate, runtime, memory, false positives, and false
   negatives across epochs;
8. retain unresolved disagreement cases as UNKNOWN.

The study should produce both an MNCDS development record and an MNCS bundle for the
selected machine-native artifact. This will test whether the two specifications bind
cleanly in a realistic workflow.

## Acceptance gate

MNCDS 0.1 should remain Draft until all of the following are true:

- the Python implementation and corpus pass CI;
- an independent corpus consumer publishes normalized agreement;
- the recursive two-epoch harness study is reproducible;
- security and privacy review finds no unresolved claim-broadening issue;
- the RFC receives the independent approvals required by governance.
