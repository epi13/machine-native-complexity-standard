# SPDX-License-Identifier: Apache-2.0

import copy
import json
from pathlib import Path
from typing import Any

from mncs_validator.validation import compare_manifests

ROOT = Path(__file__).resolve().parents[1]


def _manifest() -> dict[str, Any]:
    return json.loads((ROOT / "examples/minimal/manifest.json").read_text())


def test_pareto_dominance() -> None:
    first = _manifest()
    second = copy.deepcopy(first)
    second["complexity_profile"]["memory_bytes"] = 100
    second["complexity_profile"]["validation_cost_seconds"] = 2
    result = compare_manifests(first, second)
    assert result.relation == "A_DOMINATES_B"


def test_incomparable_candidates_are_explained() -> None:
    first = _manifest()
    second = copy.deepcopy(first)
    first["complexity_profile"]["throughput"] = 2_000_000
    second["complexity_profile"]["memory_bytes"] = 0
    first["complexity_profile"]["memory_bytes"] = 100
    result = compare_manifests(first, second)
    assert result.relation == "INCOMPARABLE"
    assert "hidden weights" in result.explanation


def test_different_contracts_are_not_compared() -> None:
    first = _manifest()
    second = copy.deepcopy(first)
    second["component"]["contract_id"] = "different"
    assert compare_manifests(first, second).relation == "DIFFERENT_CONTRACT"
