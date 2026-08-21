# Installation profiles

Profiles are planning shortcuts. The dependency graph still comes from
`family/mncs-family.v0.1.json`.

| Profile | Intended contents |
| --- | --- |
| `core` | MNCS validator. Optional Rust validator if Rust is present. |
| `developer` | Core, MNCDS, Fabric, Commons, Harness, Forge, Control MCP. |
| `worker` | Fabric worker checkout and preflight. Enrollment remains Fabric-owned. |
| `research` | Developer plus language, studies, MNEL, RAVEL, Atlas, lineage, rights. |
| `full` | Every registered component this host can support. |

Optional components are skipped when required tools are missing rather than
reported as PASS. Unsupported platforms are `deferred` or `blocked`, never
silently installed.

```bash
mncs components --profile developer --json
mncs bootstrap --profile worker --plan --json
mncs bootstrap --component mncs-atlas --plan --json
```
