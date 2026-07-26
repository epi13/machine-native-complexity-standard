#!/usr/bin/env python3
"""Mock structural provider for protocol tests; it performs no production analysis."""

# SPDX-License-Identifier: Apache-2.0

from mncs_provider_sdk import AnalysisResponse, Capabilities, ProviderIdentity, provider_main

IDENTITY = ProviderIdentity("mncs-mock-structural", "0.2.0", "example:mock-structural")
CAPABILITIES = Capabilities(IDENTITY, ["mock-structural"])


def handle(request: dict[str, object]) -> dict[str, object]:
    return AnalysisResponse(
        str(request.get("request_id", "")),
        IDENTITY,
        "UNKNOWN",
        "mock provider cannot establish a structural claim",
        limitations=["No source graph is constructed; this is a framing example."],
    ).as_dict()


if __name__ == "__main__":
    raise SystemExit(provider_main(IDENTITY, CAPABILITIES, handle))
