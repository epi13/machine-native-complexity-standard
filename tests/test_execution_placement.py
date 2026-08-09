# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from mncs_validator.cli import main
from mncs_validator.placement import validate_placement_value

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "experimental/execution-placement/fixtures/valid/sequential-offload.json"
CORPUS_INDEX = ROOT / "experimental/execution-placement/fixtures/corpus-index.json"
BASE: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))


def _record(
    *, execution: str = "PASS", placement: str = "PASS", resources: str = "PASS"
) -> dict[str, Any]:
    value = copy.deepcopy(BASE)
    value["results"] = {
        "execution": execution,
        "placement": placement,
        "resource_policy": resources,
        "status": "FAIL"
        if "FAIL" in {execution, placement, resources}
        else ("UNKNOWN" if "UNKNOWN" in {execution, placement, resources} else "PASS"),
    }
    return value


def _cpu(value: dict[str, Any]) -> None:
    value["requested_policy"]["mode"] = "cpu"
    value["requested_policy"]["backend"] = None
    value["requested_policy"]["limits"] = [
        item
        for item in value["requested_policy"]["limits"]
        if item["resource"] != "accelerator-memory"
    ]
    value["resource_policy"]["limits"] = [
        item
        for item in value["resource_policy"]["limits"]
        if item["resource"] != "accelerator-memory"
    ]
    value["capability_observations"].update(
        {
            "configured": "not-configured",
            "discovered": "unknown",
            "execution_probe": "UNKNOWN",
            "backend": None,
        }
    )
    value["actual_execution"].update(
        {"placement": "cpu-only", "backend": None, "attempted_placements": ["cpu-only"]}
    )
    value["residency"]["weight_placement"] = "host-ram"
    value["placement_evidence"] = [
        {
            **value["placement_evidence"][0],
            "evidence_id": "witness.cpu-runtime-v1",
            "kind": "runtime-hook",
            "source_id": "runtime.accelerator-adapter-v1",
            "observed_placement": "cpu-only",
        }
    ]
    value["measurements"] = [
        item for item in value["measurements"] if "accelerator" not in item["metric"]
    ]


def _full_accelerator(value: dict[str, Any]) -> None:
    value["requested_policy"]["mode"] = "accelerator"
    value["actual_execution"].update(
        {"placement": "full-accelerator", "attempted_placements": ["full-accelerator"]}
    )
    value["residency"]["weight_placement"] = "accelerator"
    value["placement_evidence"] = [
        {**item, "observed_placement": "full-accelerator"} for item in value["placement_evidence"]
    ]


def _auto_budget(value: dict[str, Any]) -> None:
    value["requested_policy"]["mode"] = "auto"
    value["requested_policy"]["allowed_transitions"] = ["full-accelerator->sequential-offload"]
    value["actual_execution"]["attempted_placements"] = ["full-accelerator", "sequential-offload"]
    value["fallback"].update(
        {
            "allowed_transitions": ["full-accelerator->sequential-offload"],
            "observed_transitions": ["full-accelerator->sequential-offload"],
            "cause": "budget-insufficient",
        }
    )


def _auto_oom_to_cpu(value: dict[str, Any]) -> None:
    value["requested_policy"]["mode"] = "auto"
    value["actual_execution"].update(
        {
            "placement": "cpu-only",
            "backend": None,
            "attempted_placements": ["full-accelerator", "sequential-offload", "cpu-only"],
        }
    )
    value["residency"]["weight_placement"] = "host-ram"
    value["fallback"].update(
        {
            "allowed_transitions": [
                "full-accelerator->sequential-offload",
                "sequential-offload->cpu",
            ],
            "observed_transitions": [
                "full-accelerator->sequential-offload",
                "sequential-offload->cpu",
            ],
            "cause": "resource-exhaustion",
        }
    )
    value["placement_evidence"] = [
        {
            **value["placement_evidence"][0],
            "evidence_id": "witness.cpu-fallback-v1",
            "kind": "provider-witness",
            "source_id": "provider.local-vision-v1",
            "observed_placement": "cpu-only",
        }
    ]


def _optional_metrics(value: dict[str, Any]) -> None:
    value["measurements"] = [
        item
        for item in value["measurements"]
        if item["metric"] not in {"offload-count", "model-storage-bytes"}
    ]


@pytest.mark.parametrize(
    ("name", "mutator", "expected", "status"),
    [
        ("cpu-only", _cpu, "PASS", "PASS"),
        ("full-accelerator", _full_accelerator, "PASS", "PASS"),
        ("sequential-offload", lambda value: None, "PASS", "PASS"),
        ("auto-selects-sequential", _auto_budget, "PASS", "PASS"),
        ("auto-oom-recovery-to-cpu", _auto_oom_to_cpu, "PASS", "PASS"),
        ("optional-metrics-unknown-absent", _optional_metrics, "PASS", "PASS"),
        (
            "accelerator-without-probe",
            lambda value: (
                value["capability_observations"].update({"execution_probe": "UNKNOWN"}),
                value["results"].update({"placement": "UNKNOWN", "status": "UNKNOWN"}),
            ),
            "UNKNOWN",
            "UNKNOWN",
        ),
        (
            "sequential-without-witness",
            lambda value: (
                value.update({"placement_evidence": []}),
                value["results"].update({"placement": "UNKNOWN", "status": "UNKNOWN"}),
            ),
            "UNKNOWN",
            "UNKNOWN",
        ),
        (
            "resource-cap-exceeded",
            lambda value: (
                value["measurements"][0].update({"value": 400000001}),
                value["results"].update({"resource_policy": "FAIL", "status": "FAIL"}),
            ),
            "FAIL",
            "FAIL",
        ),
        (
            "partial-resource-observation",
            lambda value: (
                value.update(
                    {
                        "measurements": [
                            item
                            for item in value["measurements"]
                            if item["metric"] not in {"process-rss-bytes", "host-memory-peak-bytes"}
                        ]
                    }
                ),
                value["results"].update({"resource_policy": "UNKNOWN", "status": "UNKNOWN"}),
            ),
            "UNKNOWN",
            "UNKNOWN",
        ),
    ],
)
def test_execution_placement_fixture_matrix(
    name: str, mutator: Callable[[dict[str, Any]], object], expected: str, status: str
) -> None:
    value = _record()
    mutator(value)
    report = validate_placement_value(value, target=name)
    assert report.category == expected
    assert report.computed_status == status


def test_fixture_index_is_complete_and_explicit() -> None:
    index = json.loads(CORPUS_INDEX.read_text(encoding="utf-8"))
    assert index["schema_version"] == "0.1-experimental-corpus"
    assert len(index["cases"]) == 20
    assert {item["expected"] for item in index["cases"]} == {
        "PASS",
        "FAIL",
        "UNKNOWN",
        "INVALID",
    }


@pytest.mark.parametrize(
    ("name", "mutator", "code"),
    [
        (
            "explicit-cpu-accelerator",
            lambda value: (
                value["requested_policy"].update({"mode": "cpu", "backend": None}),
                value["actual_execution"].update({"placement": "full-accelerator"}),
            ),
            "REQUESTED-PLACEMENT-VIOLATED",
        ),
        (
            "explicit-accelerator-cpu",
            lambda value: (
                value["requested_policy"].update({"mode": "accelerator"}),
                value["actual_execution"].update({"placement": "cpu-only", "backend": None}),
            ),
            "REQUESTED-PLACEMENT-VIOLATED",
        ),
        (
            "auto-undeclared-transition",
            lambda value: (
                value["requested_policy"].update({"mode": "auto"}),
                value["fallback"].update(
                    {
                        "observed_transitions": ["full-accelerator->sequential-offload"],
                        "transition_authorized": True,
                    }
                ),
                value["actual_execution"].update(
                    {"attempted_placements": ["full-accelerator", "sequential-offload"]}
                ),
            ),
            "FALLBACK-NOT-AUTHORIZED",
        ),
        (
            "stale-environment",
            lambda value: value["identity_bindings"]["environment"].update(
                {"observed": "environment.changed-v2"}
            ),
            "STALE-IDENTITY-LINK",
        ),
        (
            "runtime-identity-changed",
            lambda value: value["identity_bindings"]["runtime"].update(
                {"observed": "runtime.changed-v2"}
            ),
            "STALE-IDENTITY-LINK",
        ),
        (
            "residency-confuses-offload",
            lambda value: value["residency"].update({"weight_placement": "accelerator"}),
            "RESIDENCY-CONTRADICTION",
        ),
        (
            "self-governing-conformance",
            lambda value: value.update(
                {
                    "governing_results": {
                        "mncs": {
                            "status": "PASS",
                            "record_id": value["record_id"],
                            "source_kind": "assurance-case",
                        },
                        "mncds": None,
                    }
                }
            ),
            "GOVERNING-RESULT-SELF-REFERENCE",
        ),
        (
            "reduced-precision-unprobed",
            lambda value: value["precision"].update(
                {
                    "requested": "float16",
                    "effective": "float16",
                    "probe_required": True,
                    "probe_status": "UNKNOWN",
                }
            ),
            "RESULT-MISMATCH",
        ),
        (
            "runtime-crash-during-transition",
            lambda value: (
                value["requested_policy"].update(
                    {
                        "mode": "auto",
                        "allowed_transitions": ["full-accelerator->sequential-offload"],
                    }
                ),
                value["actual_execution"].update(
                    {
                        "status": "FAIL",
                        "placement": "indeterminate",
                        "attempted_placements": ["full-accelerator", "sequential-offload"],
                    }
                ),
                value["fallback"].update(
                    {
                        "allowed_transitions": ["full-accelerator->sequential-offload"],
                        "observed_transitions": [],
                        "cause": "runtime-failure",
                        "transition_status": "FAIL",
                    }
                ),
                value["results"].update(
                    {"execution": "FAIL", "placement": "UNKNOWN", "status": "FAIL"}
                ),
            ),
            "MNCS-EXP-PLACEMENT-EXECUTION",
        ),
    ],
)
def test_adversarial_placement_cases(
    name: str, mutator: Callable[[dict[str, Any]], object], code: str
) -> None:
    value = _record()
    mutator(value)
    report = validate_placement_value(value, target=name)
    assert (
        report.category == "INVALID"
        if name != "runtime-crash-during-transition"
        else report.category == "FAIL"
    )
    findings = {issue.code for issue in report.issues} | set(report.rule_results)
    assert code in findings


@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: value["claim_boundary"].update({"conformance_claim": "asserted"}),
        lambda value: value["claim_boundary"].update({"independence_claim": "asserted"}),
        lambda value: value["residency"].update({"weight_placement": "accelerator"}),
    ],
)
def test_claim_boundary_and_residency_schema_rejections(
    mutator: Callable[[dict[str, Any]], object],
) -> None:
    value = _record()
    mutator(value)
    report = validate_placement_value(value)
    assert report.category == "INVALID"


def test_nonfinite_and_invalid_unit_are_rejected() -> None:
    value = _record()
    value["measurements"][0]["value"] = float("nan")
    report = validate_placement_value(value)
    assert report.category == "INVALID"
    value = _record()
    value["resource_policy"]["limits"][0]["unit"] = "MiB"
    report = validate_placement_value(value)
    assert report.category == "INVALID"


def test_validate_placement_cli_and_require_pass(capsys: object) -> None:
    assert main(["validate-placement", str(FIXTURE), "--json", "--require-pass"]) == 0
    result = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert result["category"] == "PASS"
    unknown = copy.deepcopy(BASE)
    unknown["placement_evidence"] = []
    unknown["results"].update({"placement": "UNKNOWN", "status": "UNKNOWN"})
    unknown_path = ROOT / "experimental/execution-placement/fixtures/unknown/no-witness.json"
    unknown_path.parent.mkdir(parents=True, exist_ok=True)
    unknown_path.write_text(json.dumps(unknown), encoding="utf-8")
    try:
        assert main(["validate-placement", str(unknown_path), "--require-pass"]) == 3
        capsys.readouterr()  # type: ignore[attr-defined]
    finally:
        unknown_path.unlink()
