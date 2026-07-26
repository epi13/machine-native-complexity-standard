#!/usr/bin/env python3
"""Example FAIL result with a compact, non-executable witness."""

# SPDX-License-Identifier: Apache-2.0

from mncs_provider_sdk import (
    AnalysisResponse,
    Capabilities,
    ProviderIdentity,
    Witness,
    provider_main,
)

IDENTITY = ProviderIdentity("mncs-fail-witness", "0.2.0", "example:fail-witness")
CAPABILITIES = Capabilities(IDENTITY, ["fixture-failure"])


def handle(request: dict[str, object]) -> dict[str, object]:
    return AnalysisResponse(
        str(request.get("request_id", "")),
        IDENTITY,
        "FAIL",
        "fixture demonstrates a compact counterexample",
        [Witness("counterexample", "input 0 violates declared positive-only result", ["input:0"])],
        ["Deliberate example failure; not a production analyzer."],
    ).as_dict()


if __name__ == "__main__":
    raise SystemExit(provider_main(IDENTITY, CAPABILITIES, handle))
