# Deployment

Deployment here means **operational bring-up** of MNCS-family software on a
host. It is not promotion of an MNCS claim.

## Host classes

- **Controller / developer workstation** — Fedora is first-class. Developer
  profile plus optional Control MCP.
- **Fabric worker** — Linux, Windows, or Raspberry Pi OS. Worker profile.
- **Research workstation** — Research or full profile.

## Privilege

Prefer user-level virtualenvs and user systemd units. Bootstrap never stores
passwords and never auto-elevates. Privileged actions are explained in the plan
and left to the operator.

## Receipts

Each apply writes `~/.local/state/mncs/bootstrap/receipts/latest.json`. The
receipt schema is operational. Missing evidence remains `UNKNOWN` in MNCS;
bootstrap does not relabel it.

See [Fabric deployment](fabric-deployment.md) and [platform support](platform-support.md).
