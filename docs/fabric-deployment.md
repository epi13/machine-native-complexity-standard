# Fabric deployment

Bootstrap can install the Fabric **package** and plan worker bring-up. It does
not implement a shadow controller.

Use Fabric's own controller, enrollment, and worker contracts.

```bash
mncs deploy worker --plan --json
```

A worker plan typically:

1. clones `mncs-fabric` into the workspace;
2. creates a user virtualenv and installs the package;
3. reports remaining operator actions for commissioning.

It will **not**:

- invent TLS certificates or HMAC secrets
- auto-enroll a worker
- rewrite controller ledgers
- disable containment
- assume `/home/epi13/Documents/Projects`

Linux user-systemd installer:
`deploy/systemd/install-or-update-controller.sh` and
`deploy/systemd/WORKER_INSTALL.md` in the Fabric repository.

Windows worker launch remains Fabric-owned
(`scripts/windows_worker_launcher.py`). Raspberry Pi / ARM workers use Fabric's
explicit local configuration, not bootstrap autodetection of a controller.

Live inspection of the current lab controller showed Fabric `0.2.0a31` in
service mode with Windows (`collamore02-windows`) and Linux
(`fabric-worker-01`) workers available. Worker rendezvous was still `PLANNED`
on that controller. Treat those facts as environment observations, not as
universal defaults.
