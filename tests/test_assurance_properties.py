"""Bounded generated and hand-written assurance graph properties."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from mncs_validator.assurance import (
    AssuranceValidationReport,
    aggregate_status,
    derive_claim_statuses,
    derive_revalidation,
    freshness_status,
    graph_impact_closure,
    validate_assurance_value,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads(
    (ROOT / "examples/release-candidate-0.3/assurance-case.json").read_text(encoding="utf-8")
)

settings.register_profile(
    "mncs_ci",
    max_examples=60,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
    print_blob=True,
)
settings.load_profile("mncs_ci")

STATUSES = st.sampled_from(["PASS", "UNKNOWN", "FAIL"])


def _claim(claim_id: str, status: str = "PASS", *, retired: bool = False) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "base_status": status,
        "freshness": {"status": "PASS", "valid_until": "2030-01-01T00:00:00Z"},
        "retired": retired,
    }


def _dependency(
    source: str,
    target: str,
    *,
    required: bool = True,
    interface: str = "PASS",
    environment: str = "PASS",
) -> dict[str, Any]:
    return {
        "source_claim_id": source,
        "target_claim_id": target,
        "required": required,
        "interface_compatibility": interface,
        "environment_compatibility": environment,
        "correlated_failure_group_ids": [],
    }


@given(st.lists(STATUSES, min_size=1, max_size=12))
def test_status_lattice_monotonicity(statuses: list[str]) -> None:
    before = aggregate_status(statuses)
    assert aggregate_status([*statuses, "FAIL"]) == "FAIL"
    with_unknown = aggregate_status([*statuses, "UNKNOWN"])
    assert not (before == "UNKNOWN" and with_unknown == "PASS")
    assert not (before == "FAIL" and with_unknown != "FAIL")


@given(st.permutations((0, 1)))
def test_ordering_invariance_for_claims_and_normalized_report(order: list[int]) -> None:
    value = copy.deepcopy(BASE)
    value["claims"] = [value["claims"][index] for index in order]
    value["dependencies"] = list(reversed(value["dependencies"]))
    value["correlated_failure_groups"] = list(reversed(value["correlated_failure_groups"]))
    report = validate_assurance_value(value, at=datetime(2026, 8, 1, tzinfo=UTC))
    baseline = validate_assurance_value(BASE, at=datetime(2026, 8, 1, tzinfo=UTC))
    assert report.category == baseline.category
    assert sorted(item.code for item in report.issues + report.warnings) == sorted(
        item.code for item in baseline.issues + baseline.warnings
    )
    assert report.rule_results == baseline.rule_results


@given(target=STATUSES, interface=STATUSES, environment=STATUSES, retired=st.booleans())
def test_required_dependency_propagation(
    target: str,
    interface: str,
    environment: str,
    retired: bool,
) -> None:
    claims = {
        "source": _claim("source"),
        "target": _claim("target", target, retired=retired),
    }
    derived = derive_claim_statuses(
        claims,
        [
            _dependency(
                "source",
                "target",
                interface=interface,
                environment=environment,
            )
        ],
        {},
        datetime(2026, 8, 1, tzinfo=UTC),
    )
    expected_target = "FAIL" if retired or target == "FAIL" else target
    assert derived["source"] == aggregate_status(
        ["PASS", "PASS", expected_target, interface, environment]
    )


@pytest.mark.parametrize("optional_status", ["UNKNOWN", "FAIL"])
def test_optional_dependency_is_visible_without_automatic_propagation(
    optional_status: str,
) -> None:
    claims = {
        "source": _claim("source"),
        "target": _claim("target", optional_status),
    }
    dependencies = [_dependency("source", "target", required=False)]
    derived = derive_claim_statuses(
        claims,
        dependencies,
        {},
        datetime(2026, 8, 1, tzinfo=UTC),
    )
    assert derived["source"] == "PASS"

    value = copy.deepcopy(BASE)
    value["dependencies"][0]["required"] = False
    value["claims"][1]["base_status"] = optional_status
    value["claims"][1]["status"] = optional_status
    report = validate_assurance_value(value)
    assert "MNCS-03-OPTIONAL-DEPENDENCY-UNDISCLOSED" in {issue.code for issue in report.issues}


def test_cycle_and_missing_reference_never_pass() -> None:
    cycle = copy.deepcopy(BASE)
    cycle["dependencies"].append(
        {
            **cycle["dependencies"][0],
            "dependency_id": "dependency.reverse",
            "source_claim_id": "claim.component",
            "target_claim_id": "claim.system",
        }
    )
    cycle_report = validate_assurance_value(cycle)
    assert cycle_report.category == "INVALID"
    assert "MNCS-03-DEPENDENCY-CYCLE" in {issue.code for issue in cycle_report.issues}

    missing = copy.deepcopy(BASE)
    missing["dependencies"][0]["target_claim_id"] = "claim.missing"
    missing_report = validate_assurance_value(missing)
    assert missing_report.category == "INVALID"
    assert "MNCS-03-REFERENCE-MISSING" in {issue.code for issue in missing_report.issues}


@given(offset_seconds=st.integers(min_value=1, max_value=86_400))
def test_freshness_monotonicity(offset_seconds: int) -> None:
    expiry = datetime(2027, 1, 1, tzinfo=UTC)
    value = {"status": "PASS", "valid_until": expiry.isoformat()}
    assert freshness_status(value, expiry - timedelta(seconds=1)) == "PASS"
    assert freshness_status(value, expiry + timedelta(seconds=offset_seconds)) != "PASS"


@given(size=st.integers(min_value=1, max_value=10), changed=st.integers(min_value=0, max_value=9))
def test_graph_impact_closure_covers_every_required_upstream(
    size: int,
    changed: int,
) -> None:
    changed %= size
    dependencies = [
        _dependency(f"claim-{index}", f"claim-{index + 1}") for index in range(size - 1)
    ]
    assert graph_impact_closure({f"claim-{changed}"}, dependencies) == {
        f"claim-{index}" for index in range(changed + 1)
    }


def test_transitive_graph_impact_regression_rejects_direct_only_scope() -> None:
    """This input was incorrectly accepted before required closure was computed."""

    value = copy.deepcopy(BASE)
    value["material_changes"] = [
        {
            "change_id": "change.component-v2",
            "dimension": "artifact",
            "old_identity": "artifact.component-v1",
            "new_identity": "artifact.component-v2",
            "material": True,
            "rationale": "Required component changed.",
            "affected_claim_ids": ["claim.component"],
        }
    ]
    value["evidence_impact"].update(
        {
            "affected_claim_ids": ["claim.component"],
            "invalidated_evidence_ids": ["evidence.component-v1"],
            "required_new_evidence_ids": ["evidence.component-v2"],
        }
    )
    value["revalidation"].update(
        {
            "mode": "partial",
            "scope_claim_ids": ["claim.component"],
            "covered_change_ids": ["change.component-v2"],
            "retained_evidence_ids": ["evidence.system-v1", "evidence.shared-v1"],
            "new_evidence_ids": ["evidence.component-v2"],
            "performed_at": "2026-08-01T00:00:00Z",
        }
    )
    report = validate_assurance_value(value)
    assert report.category == "INVALID"
    codes = {issue.code for issue in report.issues}
    assert "MNCS-03-IMPACT-SCOPE-INCOMPLETE" in codes
    assert "MNCS-03-REVALIDATION-RESULT-MISMATCH" in codes


@given(omission=st.sampled_from(["claim", "change", "invalidated", "new"]))
def test_partial_revalidation_requires_every_declared_input(omission: str) -> None:
    dependencies = [_dependency("root", "dependency")]
    value: dict[str, Any] = {
        "material_changes": [
            {
                "change_id": "change-1",
                "material": True,
                "affected_claim_ids": ["dependency"],
            }
        ],
        "evidence_impact": {
            "status": "PASS",
            "invalidated_evidence_ids": ["old-evidence"],
            "required_new_evidence_ids": ["new-evidence"],
        },
        "revalidation": {
            "mode": "partial",
            "scope_claim_ids": ["root", "dependency"],
            "covered_change_ids": ["change-1"],
            "retained_evidence_ids": [],
            "new_evidence_ids": ["new-evidence"],
            "status": "PASS",
        },
    }
    if omission == "claim":
        value["revalidation"]["scope_claim_ids"].remove("root")
    elif omission == "change":
        value["revalidation"]["covered_change_ids"] = []
    elif omission == "invalidated":
        value["revalidation"]["retained_evidence_ids"] = ["old-evidence"]
    else:
        value["revalidation"]["new_evidence_ids"] = []
    status, _, _ = derive_revalidation(value, {"root", "dependency"}, dependencies)
    assert status == "UNKNOWN"


@given(missing=st.sampled_from(["root", "dependency"]))
def test_full_revalidation_requires_complete_claim_scope(missing: str) -> None:
    value: dict[str, Any] = {
        "material_changes": [
            {"change_id": "change-1", "material": True, "affected_claim_ids": ["dependency"]}
        ],
        "evidence_impact": {
            "status": "PASS",
            "invalidated_evidence_ids": [],
            "required_new_evidence_ids": [],
        },
        "revalidation": {
            "mode": "full",
            "scope_claim_ids": ["root", "dependency"],
            "covered_change_ids": ["change-1"],
            "retained_evidence_ids": [],
            "new_evidence_ids": [],
            "status": "PASS",
        },
    }
    value["revalidation"]["scope_claim_ids"].remove(missing)
    status, _, _ = derive_revalidation(
        value,
        {"root", "dependency"},
        [_dependency("root", "dependency")],
    )
    assert status == "UNKNOWN"


def test_retired_required_claim_cannot_support_pass() -> None:
    claims = {"root": _claim("root"), "dependency": _claim("dependency", retired=True)}
    derived = derive_claim_statuses(
        claims,
        [_dependency("root", "dependency")],
        {},
        datetime(2026, 8, 1, tzinfo=UTC),
    )
    assert derived["dependency"] == "FAIL"
    assert derived["root"] == "FAIL"


@given(category=STATUSES)
def test_report_serialization_round_trip_is_stable(category: str) -> None:
    report = AssuranceValidationReport(target="$", kind="assurance")
    report.rule("example", category)  # type: ignore[arg-type]
    normalized = report.as_dict()
    assert json.loads(json.dumps(normalized, sort_keys=True)) == normalized
