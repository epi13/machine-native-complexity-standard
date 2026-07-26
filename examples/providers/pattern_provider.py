#!/usr/bin/env python3
"""Deterministic example only: checks declared text patterns, not semantic correctness."""

# SPDX-License-Identifier: Apache-2.0

from mncs_provider_sdk import (
    AnalysisResponse,
    Capabilities,
    ProviderIdentity,
    Witness,
    provider_main,
)

IDENTITY = ProviderIdentity("mncs-pattern-example", "0.2.0", "example:pattern")
CAPABILITIES = Capabilities(IDENTITY, ["declared-pattern"])


def handle(request: dict[str, object]) -> dict[str, object]:
    component = request.get("component", {})
    text = str(component.get("text", "")) if isinstance(component, dict) else ""
    pattern = str(component.get("pattern", "")) if isinstance(component, dict) else ""
    found = bool(pattern) and pattern in text
    return AnalysisResponse(
        str(request.get("request_id", "")),
        IDENTITY,
        "PASS" if found else "FAIL",
        "declared pattern found" if found else "declared pattern absent",
        []
        if found
        else [Witness("pattern", "required literal was absent", data={"pattern": pattern})],
        ["Example performs literal matching only."],
    ).as_dict()


if __name__ == "__main__":
    raise SystemExit(provider_main(IDENTITY, CAPABILITIES, handle))
