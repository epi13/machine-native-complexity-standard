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
| Recursive analyzer or harness improvement across epochs | `studies/recursive-analyzer` and RC development record | Internally reproducible; external custody UNKNOWN |
| D4 rollback, regeneration drill, retirement | D4 reference record and rejection tests | Implemented |
| Independent validator agreement | `independent/rc-consumer` and combined RC corpus | 74/74 local agreement; operator/organization UNKNOWN |

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
- untested rollback; and
- failed regeneration drills.

## Independent implementation evidence

RFC 0004 must not be accepted solely because the reference Python validator agrees with
its own tests. Before acceptance, at least one independently implemented consumer should:

1. parse `mncds-conformance-corpus/corpus.json` without importing the Python validator;
2. apply the declared mutations;
3. produce normalized validity, status, and issue-class outcomes;
4. publish an agreement report including every disagreement and unsupported rule; and
5. preserve unsupported behavior as UNKNOWN rather than PASS.

The checked-in Rust implementation satisfies the source and executable diversity
requirements for the bounded RC corpus. It does not establish independent operation or
organizational independence; those remain external evidence gates.

## Recursive analyzer and harness study

The checked-in bounded study freezes two analyzer identities, converts epoch-one blind
spots into regression fixtures, and uses a fresh developer-withheld final partition.
Joern is not a normative dependency.

The study does:

1. freeze the original analyzer or harness, corpus, environment, and evaluation policy as
   epoch one;
2. evaluate at least two competing implementation or analysis ideas;
3. record false positives, false negatives, incorrect PASS, UNKNOWN, crashes, timeouts,
   runtime, memory, determinism, and diagnostic utility;
4. convert discovered disagreements and blind spots into classified regression fixtures;
5. create a newly identified epoch-two analyzer or harness;
6. rerun the analyzer regression corpus;
7. evaluate the frozen epoch-two candidate using fresh developer-withheld inputs;
8. compare detection quality, evidence quality, resource cost, and reproducibility across
   epochs; and
9. retain unresolved disagreement cases as UNKNOWN.

The experimental Machine-Native Evidence Analyzer described in
`docs/machine-native-evidence-analyzer.md` is one possible epoch-two implementation. It is
not required for conformance and must be evaluated as an untrusted provider.

The study produces an MNCDS development record and an offline MNCS assurance resolution
set. Internal selection is PASS, while MNCS and MNCDS remain UNKNOWN because external
independence and protected custody are absent.

## Acceptance gate

MNCDS 0.1 should remain Draft until all of the following are true:

- the Python implementation and corpus pass CI;
- an independent corpus consumer publishes normalized agreement;
- the recursive two-epoch analyzer or harness study is reproducible;
- security and privacy review finds no unresolved claim-broadening issue; and
- the RFC receives the independent approvals required by governance.
