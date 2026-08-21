# Getting started

MNCS is the Machine-Native Complexity Standard: an experimental, tool-neutral
contract for accepting generated or machine-optimized implementations through
bounded evidence.

It is **not** an installer brand, an accredited certification, or a guarantee
that installed software is conformant.

> Human readability is relocated, not eliminated.

## Choose a path

1. **Understand the standard** — [Introduction](introduction.md), then
   [Quickstart](quickstart.md) to validate an example bundle.
2. **Install family software** — [Installation](installation.md) and
   [Bootstrap](bootstrap.md).
3. **See the ecosystem** — [MNCS family](family.md) and
   [Atlas](https://github.com/epi13/mncs-atlas).
4. **Arrive as an agent** — [AI agent bootstrap](ai-agent-bootstrap.md).

## Smallest useful commands

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
mncs version --json
mncs family --json
mncs doctor --json
mncs bootstrap --profile core --plan --json
```

A planned or completed bootstrap is an operational result only. It does not
create PASS, certification, independent evidence, protected custody, governance
approval, or promotion authority.
