# AI agent bootstrap

Prefer structured CLI output over scraping README prose.

## What this repository is

MNCS is the normative implementation-evidence standard. You may add operational
bootstrap code, documentation, and tests. You must not reinterpret frozen
specifications, rewrite historical evidence, or treat an install receipt as
PASS.

## Inspect first

```bash
mncs describe --json
mncs family --json
mncs doctor --json
mncs bootstrap --profile developer --plan --json
```

If MNCS Control, Forge, Fabric, Harness, or Commons MCP/tools are available in
the session, inspect those live surfaces before assuming topology from names.

## Non-interactive install

```bash
mncs bootstrap --profile developer --yes --json --workspace "$MNCS_WORKSPACE"
```

Never use interactive prompts as the only API. Never pipe remote scripts to
`sudo`. Never invent secrets.

## Honesty

- Missing evidence stays `UNKNOWN`.
- Unsupported platforms are `deferred` or `unsupported`.
- Compatibility across family versions is `UNKNOWN` until a matrix is published.
- Forge is not a package manager.
- Commons is not an installer database.
- Installation is not conformance.

## What you may not modify

- Frozen specs under `spec/`
- Historical fixtures, corpora, and study evidence
- MNCDS meaning (owned by the MNCDS repository)
- Fabric/Forge/Commons authority boundaries
