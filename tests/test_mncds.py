# SPDX-License-Identifier: Apache-2.0

import copy
import json
from pathlib import Path
from typing import Any

from mncs_validator.mncds import validate_development_value
from mncs_validator.schemas import schema_errors

ROOT = Path(__file__).resolve().parents[1]


def _d4_record() -> dict[str, Any]:
    path = ROOT / "examples/mncds-d4/development-record.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _d1_record() -> dict[str, Any]:
    value = copy.deepcopy(_d4_record())
    value["profile"] = "MNCDS-D1"
    value["charter"]["planned_mncs_level"] = None
    value["partitions"]["holdout_id"] = None
    value["evaluators"] = [value["evaluators"][0]]
    value["candidates"][1]["evaluator_results"] = value["candidates"][1][
        "evaluator_results"
    ][:3]
    value["reproducibility"] = {
        "class": "NONE",
        "seeds_preserved": False,
        "protocol": "Candidate identities and generator configuration are preserved.",
        "measurement_repetitions": 1,
    }
    value["mncs_binding"] = None
    value["release_controls"] = None
    return value


def _d2_record() -> dict[str, Any]:
    value = _d1_record()
    value["profile"] = "MNCDS-D2"
    value["reproducibility"] = {
        "class": "SEEDED",
        "seeds_preserved": True,
        "protocol": "Replay the pinned environment and recorded seed set.",
        "measurement_repetitions": 3,
    }
    return value


def _d3_record() -> dict[str, Any]:
    value = copy.deepcopy(_d4_record())
    value["profile"] = "MNCDS-D3"
    value["release_controls"] = None
    return value


def test_development_record_schema_is_packaged() -> None:
    assert schema_errors(_d4_record(), "mncds-development-record") == []


def test_cumulative_profiles_pass() -> None:
    for record in (_d1_record(), _d2_record(), _d3_record(), _d4_record()):
        report = validate_development_value(record)
        assert report.valid, report.as_dict()
        assert report.computed_status == "PASS"


def test_generator_cannot_modify_evaluator_or_threshold() -> None:
    record = _d4_record()
    record["generator"]["permissions"]["modify_evaluators"] = True
    record["generator"]["permissions"]["modify_thresholds"] = True
    report = validate_development_value(record)
    assert not report.valid
    assert {issue.code for issue in report.issues} >= {
        "generator-authority-violation"
    }


def test_candidate_lineage_cycle_is_rejected() -> None:
    record = _d4_record()
    record["candidates"][0]["parent_ids"] = ["candidate-b"]
    report = validate_development_value(record)
    assert not report.valid
    assert "lineage-cycle" in {issue.code for issue in report.issues}


def test_required_unknown_cannot_be_promoted_under_reject_policy() -> None:
    record = _d4_record()
    record["candidates"][1]["evaluator_results"][0]["status"] = "UNKNOWN"
    report = validate_development_value(record)
    assert not report.valid
    assert "unknown-promoted" in {issue.code for issue in report.issues}


def test_explicit_human_review_preserves_unknown_status() -> None:
    record = _d1_record()
    record["candidates"][1]["evaluator_results"][0]["status"] = "UNKNOWN"
    record["selection"]["unknown_policy"] = "human_review"
    record["selection"]["human_review"] = {
        "reviewer_id": "authority-contract-team",
        "decision": "accept_with_unknown",
        "rationale": "Proceed only as an experimental record; no PASS claim is made.",
    }
    report = validate_development_value(record)
    assert report.valid
    assert report.computed_status == "UNKNOWN"


def test_d3_requires_independent_authority_and_executable() -> None:
    record = _d3_record()
    record["evaluators"][1]["authority_id"] = "authority-generation-team"
    record["evaluators"][1]["executable_id"] = "generator-runner-v2"
    report = validate_development_value(record)
    assert not report.valid
    codes = {issue.code for issue in report.issues}
    assert "independence-authority-conflict" in codes
    assert "independence-executable-conflict" in codes


def test_mncs_binding_must_match_selected_candidate_and_charter() -> None:
    record = _d3_record()
    record["mncs_binding"]["candidate_id"] = "candidate-a"
    record["mncs_binding"]["environment_id"] = "other-environment"
    report = validate_development_value(record)
    assert not report.valid
    assert "mncs-binding-mismatch" in {issue.code for issue in report.issues}


def test_d4_requires_passing_rollback_and_regeneration_drill() -> None:
    record = _d4_record()
    record["release_controls"]["rollback_test_status"] = "UNKNOWN"
    record["release_controls"]["regeneration_drill"]["status"] = "FAIL"
    report = validate_development_value(record)
    assert not report.valid
    codes = {issue.code for issue in report.issues}
    assert "rollback-not-tested" in codes
    assert "regeneration-drill-failed" in codes
