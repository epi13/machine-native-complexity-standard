# Contributing

MNCS welcomes implementation, documentation, schema, research, and governance
contributions. Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).

For a small correction, open an issue and pull request. Changes to normative meaning,
schemas, conformance gates, or governance require an RFC. A pull request should:

1. explain the problem and compatibility effect;
2. include tests and valid/invalid fixtures where machine behavior changes;
3. update specification and user documentation together;
4. pass `make check`; and
5. disclose relevant conflicts of interest or vendor dependencies.

Use a local virtual environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
make check
```

Sign-off is not required. By submitting intentionally, you agree that your
contribution is licensed under Apache-2.0 as described in the repository license.
Do not submit secrets, proprietary transcripts, private datasets, or evidence you
cannot redistribute.
