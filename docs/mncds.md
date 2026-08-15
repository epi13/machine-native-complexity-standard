# Machine-Native Complexity Development Specification

Development-process guidance is maintained separately by the
[Machine-Native Complexity Development Specification (MNCDS)](https://github.com/epi13/machine-native-complexity-development-specification).

MNCS asks whether a selected implementation is supported by adequate evidence.
MNCDS asks whether the process that generated, compared, selected, released,
and later replaces that implementation remained controlled and auditable.

The two claims remain separate:

```text
MNCDS-D3 / MNCS-L4
```

This repository keeps an offline consumer so an MNCS artifact can still
validate a supplied MNCDS development record:

```bash
mncds validate examples/mncds-0.1-rc/development-record.json --json
```

The consumer does not make MNCS depend on MNCDS for understanding its own
normative requirements. Read the specification, schemas, and MNCDS-owned
validator in the MNCDS repository.
