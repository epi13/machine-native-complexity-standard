# MCP bootstrapping

MNCS-family MCP servers are first-class observations, not a single “installed”
boolean.

States used by `mncs doctor --json` and `mncs describe --json`:

- `not_installed`
- `installed`
- `configured`
- `reachable`
- `healthy`
- `degraded`
- `incompatible`
- `blocked`
- `unknown`

Currently registered MCP surfaces:

- **MNCS Control MCP** (`mncs-control-mcp`, stdio, typically tunnel-supervised)
- **MNCS Forge MCP** (`mncs-forge-mcp`, stdio)
- **MNCS Commons MCP** (`mncs-commons-mcp`, stdio; consumer access is usually
  through the Harness-owned boundary)

Installing an executable is not the same as a protocol handshake or backing
subsystem health. Control tunnel credentials and organization context are
operator-supplied. This environment exposed Control as the live MCP surface;
Forge and Fabric were inspected through Control rather than as independent MCP
servers in the agent session.

```bash
mncs doctor --json
mncs family --id mncs-forge --json
```
