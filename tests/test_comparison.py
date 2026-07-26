# SPDX-License-Identifier: Apache-2.0

import copy
import json
from pathlib import Path
from typing import Any

from mncs_validator.models import ValidationReport
from mncs_validator.validation import compare_manifests, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "conformance-corpus/valid/l4-pass/manifest.json"


def _manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text())


def _report() -> ValidationReport:
    report = validate_manifest(MANIFEST_PATH)
    assert report.certification_eligible
    return report


def test_pareto_dominance_excludes_level_as_performance() -> None:
    first = _manifest()
    second = copy.deepcopy(first)
    second["comparison_profile"]["complexity"]["source_bytes"] += 100
    result = compare_manifests(first, second, first_report=_report(), second_report=_report())
    assert result.relation == "A_DOMINATES_B"
    assert all("conformance_level" not in key for key in result.dimensions)
    assert result.evidence_strength["A"].startswith("evidence-derived")


def test_incomparable_candidates_are_explained() -> None:
    first = _manifest()
    second = copy.deepcopy(first)
    first["comparison_profile"]["benefit"]["throughput_ratio"] = 2
    first["comparison_profile"]["complexity"]["source_bytes"] = 200
    second["comparison_profile"]["complexity"]["source_bytes"] = 100
    result = compare_manifests(first, second, first_report=_report(), second_report=_report())
    assert result.relation == "INCOMPARABLE"
    assert "no weights" in result.explanation


def test_comparison_compatibility_decisions() -> None:
    first = _manifest()
    second = copy.deepcopy(first)
    second["component"]["contract_id"] = "different"
    assert compare_manifests(first, second).relation == "DIFFERENT_CONTRACT"
    second = copy.deepcopy(first)
    second["acceptance_policy"]["objective"]["metric"] = "latency"
    assert (
        compare_manifests(first, second, allow_uncertified=True).relation
        == "INCOMPATIBLE_OBJECTIVE"
    )
    second = copy.deepcopy(first)
    second["acceptance_policy"]["objective"]["unit"] = "seconds"
    assert compare_manifests(first, second, allow_uncertified=True).relation == "INCOMPATIBLE_UNITS"


def test_uncertified_inputs_require_flag_and_warning() -> None:
    manifest = _manifest()
    assert compare_manifests(manifest, manifest).relation == "UNCERTIFIED_INPUT"
    result = compare_manifests(manifest, manifest, allow_uncertified=True)
    assert result.warning and "DESCRIPTIVE ONLY" in result.warning


def test_environment_and_evaluator_compatibility() -> None:
    first = _manifest()
    second = copy.deepcopy(first)
    first_report = _report()
    second_report = copy.deepcopy(first_report)
    second_report.comparison_context["environment"] = "sha256:" + "1" * 64
    assert (
        compare_manifests(
            first,
            second,
            first_report=first_report,
            second_report=second_report,
        ).relation
        == "INCOMPATIBLE_ENVIRONMENT"
    )
    second_report = copy.deepcopy(first_report)
    second_report.comparison_context["evaluator"] = "sha256:" + "2" * 64
    assert (
        compare_manifests(
            first,
            second,
            first_report=first_report,
            second_report=second_report,
        ).relation
        == "INVALID_EVIDENCE"
    )
