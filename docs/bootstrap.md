# Bootstrap

The `mncs` CLI now includes an operational family bootstrapper. It plans and
optionally applies a desired installation state from the family registry.

This is a working implementation foundation for
[RFC 0009](https://github.com/epi13/machine-native-complexity-standard/blob/main/rfcs/0009-machine-native-bootstrap-and-deployment.md)
and the [design note](machine-native-bootstrap-deployment.md). RFC 0009 remains
Draft. This engine does not change MNCS 0.2 or 0.3-rc.1 conformance semantics.

This is not a conformance engine.

## Dual interface

Humans:

```bash
mncs bootstrap
```

Agents:

```bash
mncs bootstrap --profile developer --plan --json
mncs bootstrap --profile developer --yes --json
```

`--plan` and `--dry-run` never mutate the host. `--yes` is required for
non-interactive mutation. Interactive prompts are never the only API.

## Commands

| Command | Purpose |
| --- | --- |
| `mncs family --json` | Registry, authority, profiles, components |
| `mncs components --json` | Component list |
| `mncs describe --json` | Combined self-description |
| `mncs doctor --json` | Host + observed family health |
| `mncs status --json` | Installed/observed state |
| `mncs bootstrap --plan --json` | Desired vs observed plan |
| `mncs install --profile core --yes --json` | Apply a profile |
| `mncs configure --json` | Remaining operator actions |
| `mncs repair --plan --json` | Re-plan from incomplete state |
| `mncs deploy worker --plan --json` | Fabric worker bring-up plan |
| `mncs uninstall --component ID --json` | Safe-removal limits |

## Model

1. Observe the host.
2. Observe existing checkouts, binaries, configs, units, and MCP commands.
3. Resolve a profile and dependency graph.
4. Emit a plan.
5. Optionally execute clone/venv/pip/cargo actions under the workspace.
6. Write an operational receipt.

User-level installation is preferred. Bootstrap will not `sudo`, store
passwords, invent TLS material, or publish install state into Commons.

Service enablement remains **operator-mediated** unless `--allow-services` is
set, and even then administrator privilege is refused.

## Workspace

Default workspace is `$MNCS_WORKSPACE`, then `~/.config/mncs/workspace.json`,
then `~/mncs`. The Fedora developer path
`/home/epi13/Documents/Projects` is **not** assumed.

## Shims

If Python is not installed, use `bootstrap/mncs-bootstrap.sh`
or `bootstrap/mncs-bootstrap.ps1`. Those
shims report the missing interpreter in JSON; they do not download privileged
installers.
