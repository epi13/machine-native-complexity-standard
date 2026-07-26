#!/usr/bin/env python3
"""Example that honestly returns UNKNOWN when its declared bound is exhausted."""

# SPDX-License-Identifier: Apache-2.0

from mncs_provider_sdk import AnalysisResponse, Capabilities, ProviderIdentity, provider_main

IDENTITY = ProviderIdentity("mncs-bounded-unknown", "0.2.0", "example:bounded-unknown")
CAPABILITIES = Capabilities(IDENTITY, ["bounded-analysis"])


def handle(request: dict[str, object]) -> dict[str, object]:
    return AnalysisResponse(
        str(request.get("request_id", "")),
        IDENTITY,
        "UNKNOWN",
        "analysis bound exhausted before a proof or counterexample",
        limitations=["UNKNOWN must not be promoted to PASS."],
    ).as_dict()


if __name__ == "__main__":
    raise SystemExit(provider_main(IDENTITY, CAPABILITIES, handle))
