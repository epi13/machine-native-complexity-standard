# MNCS bootstrap shims

These shims exist so a machine can report that Python is missing **without
already having a Python environment**.

- `mncs-bootstrap.sh` — POSIX (Linux, Raspberry Pi OS)
- `mncs-bootstrap.ps1` — Windows PowerShell

Once Python 3.11+ and the `mncs` CLI are available, use:

```bash
mncs bootstrap --profile developer --plan --json
mncs bootstrap --profile developer --yes --json
```

The shims never pipe remote scripts to a privileged shell and never store
credentials.
