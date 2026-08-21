# Configuration

Bootstrap configuration is local and operational.

| Location | Purpose |
| --- | --- |
| `$MNCS_WORKSPACE` | Explicit family checkout root |
| `~/.config/mncs/workspace.json` | Last selected workspace |
| `~/.local/state/mncs/bootstrap/receipts/` | Installation receipts |
| `$MNCS_FAMILY_REGISTRY` | Override family registry path |

Windows uses `%APPDATA%` / `%LOCALAPPDATA%` equivalents.

Component-owned paths remain authoritative:

- Fabric: `~/.config/mncs-fabric/`, `~/.local/state/mncs-fabric/`
- Commons: `~/.local/state/mncs-commons/`
- Harness: `~/.config/mncs-harness/config.toml`
- Control: `~/.config/mncs-control-mcp/` (secrets in mode `0600` env files)

Bootstrap never writes tunnel keys, Fabric certificates, or Commons operator
sockets.
