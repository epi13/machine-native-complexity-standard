#!/usr/bin/env python3
"""Run declared Forge workflows using limits from mncs-forge.toml."""

from __future__ import annotations

import forge_workflow as base
from forge_policy import load_forge_workflow_policy


def main() -> int:
    policy = load_forge_workflow_policy()
    base.ENVIRONMENT_ALLOWLIST = policy.environment_allowlist
    base.OUTPUT_CAP = policy.output_cap
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
