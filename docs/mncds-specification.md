# MNCDS 0.1 draft specification

The draft normative specification is maintained in
[`spec/MNCDS-v0.1-draft.md`](https://github.com/epi13/machine-native-complexity-standard/blob/main/spec/MNCDS-v0.1-draft.md).

MNCDS defines cumulative development-process profiles for controlled generation,
reproducible experimentation, independent selection, and operational regeneration. It
standardizes identities, authority boundaries, evidence partitions, candidate lineage,
selection controls, evaluator independence, release binding, rollback, regeneration,
and retirement.

The machine-readable implementation currently consists of:

- `schemas/mncds-development-record.schema.json`;
- the packaged schema exposed through `mncs schema mncds-development-record`;
- the offline `mncds validate` command;
- the cumulative D4 example;
- unit tests and the deterministic MNCDS conformance corpus.

MNCDS remains Draft under RFC 0004. The implementation makes the proposal testable but
does not bypass the repository's review, independent-approval, or interoperability
requirements.
