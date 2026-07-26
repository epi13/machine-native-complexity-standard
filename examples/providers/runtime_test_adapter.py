#!/usr/bin/env python3
"""Adapter example that converts supplied runtime-test counts into evidence."""

# SPDX-License-Identifier: Apache-2.0

from mncs_provider_sdk import AnalysisResponse, Capabilities, ProviderIdentity, provider_main

IDENTITY = ProviderIdentity("mncs-runtime-adapter", "0.2.0", "example:runtime-adapter")
CAPABILITIES = Capabilities(IDENTITY, ["runtime-test-evidence"])


def handle(request: dict[str, object]) -> dict[str, object]:
    component = request.get("component", {})
    passed = component.get("passed") if isinstance(component, dict) else None
    failed = component.get("failed") if isinstance(component, dict) else None
    if not isinstance(passed, int) or not isinstance(failed, int):
        status = "UNKNOWN"
        summary = "bounded counts were not supplied"
    else:
        status = "PASS" if passed > 0 and failed == 0 else "FAIL"
        summary = f"adapted supplied counts: passed={passed}, failed={failed}"
    return AnalysisResponse(
        str(request.get("request_id", "")),
        IDENTITY,
        status,
        summary,
        limitations=["The adapter does not execute tests or authenticate supplied counts."],
    ).as_dict()


if __name__ == "__main__":
    raise SystemExit(provider_main(IDENTITY, CAPABILITIES, handle))
