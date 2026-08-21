"""Bootstrap constants and stable exit codes."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

SCHEMA_VERSION = "mncs-family-registry.v0.1"
PLAN_SCHEMA_VERSION = "mncs-bootstrap-plan.v0.1"
RECEIPT_SCHEMA_VERSION = "mncs-bootstrap-receipt.v0.1"
HOST_SCHEMA_VERSION = "mncs-host-observation.v0.1"

BOOTSTRAP_DISCLAIMER = (
    "This record describes bootstrap operations only. It is not an MNCS "
    "conformance result, certification, independent evidence, protected custody, "
    "governance approval, PASS, or promotion authority."
)

GITHUB_OWNER = "epi13"
GITHUB_HOST = "https://github.com/epi13/"

SUPPORTED_OS = frozenset({"linux", "windows"})
DEFERRED_OS = frozenset({"macos"})

# Stable CLI exit codes. 0-3 remain reserved for the validator CLI.
EXIT_CODES = {
    "ok": 0,
    "execution_failed": 1,
    "usage": 2,
    "incomplete": 10,
    "repair_needed": 11,
    "unsupported": 12,
    "privilege": 13,
    "network": 14,
    "confirmation": 15,
}

COMMANDS = (
    "family",
    "components",
    "describe",
    "doctor",
    "status",
    "bootstrap",
    "install",
    "configure",
    "update",
    "repair",
    "deploy",
    "uninstall",
)

BINARY_NAMES = (
    "mncs",
    "mncds",
    "mncs-rs",
    "mncs-fabric",
    "mncs-harness",
    "elh",
    "mncs-forge",
    "mncs-forge-mcp",
    "mncs-control-mcp",
    "mncs-commons",
    "mncs-commons-mcp",
    "mncs-commons-service",
    "mnel",
    "ravel-fabric-agent",
)

TOOL_NAMES = (
    "git",
    "python",
    "python3",
    "rustc",
    "cargo",
    "gcc",
    "make",
    "powershell",
    "pwsh",
    "systemctl",
    "ollama",
    "podman",
    "docker",
    "bwrap",
    "nvidia-smi",
)
