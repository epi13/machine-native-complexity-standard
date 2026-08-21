# Platform support

Distinguish **implemented**, **unit-tested**, **integration-tested**,
**host-tested**, **experimental**, and **deferred**. Compiling is not support.

| Platform | Architecture | Bootstrap | Core | Developer | Fabric worker | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Fedora/Linux | x86-64 | implemented, unit-tested, host-tested | implemented | implemented (services assisted) | planned via Fabric installer | First-class development target |
| Debian-like Linux | x86-64 | implemented, unit-tested | implemented | experimental | experimental | Logic shared with Fedora; not separately host-tested here |
| Windows | x86-64 | implemented, unit-tested | implemented | partial (Control MCP unsupported) | planned via Fabric scripts | PowerShell shim present; not host-tested in this change |
| Raspberry Pi OS | ARM64 | implemented, unit-tested | implemented | experimental | experimental | Architecture paths exist; not host-tested in this change |
| macOS | any | deferred | deferred | deferred | deferred | Clean unsupported/deferred result; not pretended |

GPU detection never triggers CUDA or model downloads.

## What this change actually exercised

- Linux/Fedora x86-64 host discovery, JSON CLI, dry-run planning, and unit tests
  in the MNCS Control sandbox.
- Windows and ARM behavior through FakeProbe unit tests, not live hosts.
- Live Fabric inspection of a Windows worker and a Linux worker for contract
  awareness; bootstrap did not mutate those workers.
