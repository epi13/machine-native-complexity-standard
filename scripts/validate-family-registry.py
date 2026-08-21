#!/usr/bin/env python3
"""Deterministic family-registry validation. No network."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mncs_validator.bootstrap.registry import (  # noqa: E402
    load_family_mapping,
    validate_family_mapping,
)


def main() -> int:
    path = ROOT / "family/mncs-family.v0.1.json"
    packaged = ROOT / "src/mncs_validator/resources/family/mncs-family.v0.1.json"
    payload = load_family_mapping(path)
    errors = validate_family_mapping(payload)
    if path.read_bytes() != packaged.read_bytes():
        errors.append("packaged family registry does not match family/mncs-family.v0.1.json")
    for filename in (
        "mncs-family-registry-0.1.schema.json",
        "mncs-host-observation-0.1.schema.json",
        "mncs-bootstrap-plan-0.1.schema.json",
        "mncs-bootstrap-receipt-0.1.schema.json",
    ):
        source = ROOT / "schemas" / filename
        packaged_schema = ROOT / "src/mncs_validator/resources/schemas" / filename
        if source.read_bytes() != packaged_schema.read_bytes():
            errors.append(f"packaged schema mismatch: {filename}")
    if errors:
        print("family registry invalid:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"family registry ok: {len(payload['components'])} components")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
