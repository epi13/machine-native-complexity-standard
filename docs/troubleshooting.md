# Troubleshooting

## `mncs` is not found

Install the validator first, or run the POSIX/Windows shim in `bootstrap/`.

## Python is missing

The shim exits with code `14` and JSON `python: "missing"`. Install Python
3.11+ using the OS package manager. Bootstrap will not silently download a
toolchain.

## Plan says `network-required`

Re-run without `--no-network`, or clone the repositories yourself and re-run
`mncs doctor` so existing checkouts are observed.

## Control MCP is `configured` but not `healthy`

The binary or unit exists, but tunnel credentials, organization context, or
the user service may be missing. Bootstrap will not write `CONTROL_PLANE_API_KEY`.

## Fabric is installed but Harness reports no workers

Harness does not start Fabric. Confirm the persistent controller socket and
`mncs-fabric controller doctor`. Installation of the Python package is not
controller health.

## Language CLI named `mncs`

The language crate currently builds a binary named `mncs`, which collides with
this validator. Bootstrap builds the language crate and does not install that
binary onto PATH.

## macOS

Reported as `deferred`. Do not treat a compile as support.

## Repair

```bash
mncs repair --plan --json
mncs doctor --json
```

If bootstrap cannot repair a failure, the plan says why (`operator-required`,
`privilege-required`, `unsupported-platform`).
