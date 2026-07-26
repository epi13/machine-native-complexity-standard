# SPDX-License-Identifier: Apache-2.0

import json
import shutil
from pathlib import Path

import pytest

from mncs_validator.hashing import hash_path
from mncs_validator.validation import validate_bundle, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "conformance-corpus"


def issue_codes(report: object) -> set[str]:
    return {issue.code for issue in report.issues}  # type: ignore[attr-defined]


def test_valid_manifest_derives_gates_and_evidence_graph() -> None:
    report = validate_manifest(ROOT / "examples/http-chunked-decoder/manifest.json")
    assert report.valid, report.as_dict()
    assert report.computed_status == "PASS"
    assert report.gate_statuses["measurement_valid"].status == "PASS"
    assert report.gate_statuses["benefit_threshold"].evidence_ids == ["performance-primary"]
    assert "gate-behavioral" in report.evidence_graph["manifest"]
    assert "identity-evaluator" in report.evidence_graph["gate-behavioral"]


@pytest.mark.parametrize(
    ("fixture", "expected_code"),
    [
        ("copied-pass-without-evidence", "schema"),
        ("missing-gate-evidence", "unindexed-evidence"),
        ("stale-candidate-hash", "stale-candidate-hash"),
        ("stale-reference-hash", "stale-reference-hash"),
        ("stale-evaluator-hash", "identity-hash-mismatch"),
        ("conflicting-evidence-ids", "duplicate-evidence-id"),
        ("duplicate-path-conflicting-hashes", "conflicting-evidence-path"),
        ("performance-other-candidate", "performance-candidate-mismatch"),
        ("objective-mismatch", "performance-objective-metric-mismatch"),
        ("unit-mismatch", "performance-unit-mismatch"),
        ("nonfinite-samples", "invalid-json"),
        ("malformed-timestamps", "malformed-timestamp"),
        ("unknown-treated-as-pass", "status-mismatch"),
        ("final-status-mismatch", "status-mismatch"),
        ("level-missing-lower-evidence", "schema"),
        ("extension-redefines-core", "extension-shadowing"),
        ("path-escape", "schema"),
        ("symlink-escape", "unsafe-path"),
        ("unindexed-required-evidence", "unindexed-evidence"),
    ],
)
def test_invalid_conformance_fixture(fixture: str, expected_code: str) -> None:
    report = validate_bundle(CORPUS / "invalid" / fixture)
    assert not report.valid, report.as_dict()
    assert expected_code in issue_codes(report), report.as_dict()


def test_valid_fail_and_unknown_are_not_invalid() -> None:
    failed = validate_bundle(CORPUS / "valid/final-fail")
    unknown = validate_bundle(CORPUS / "valid/final-unknown")
    assert failed.valid and failed.computed_status == "FAIL"
    assert unknown.valid and unknown.computed_status == "UNKNOWN"
    assert not failed.certification_eligible
    assert not unknown.certification_eligible


def test_level_fixtures_pass_cumulatively() -> None:
    for level in range(1, 6):
        report = validate_bundle(CORPUS / f"valid/l{level}-pass")
        assert report.certification_eligible, report.as_dict()
        expected = {
            "behavioral",
            "compiler_matrix",
        }
        if level >= 2:
            expected |= {"safety", "resource_bounds", "mutation"}
        if level >= 3:
            expected.add("structural")
        if level >= 4:
            expected |= {"measurement_valid", "benefit_threshold", "worst_regression"}
        if level == 5:
            expected |= {
                "holdout",
                "regeneration",
                "provenance",
                "reproducibility",
                "post_certification_identity",
            }
        assert set(report.gate_statuses) == expected


def test_performance_threshold_is_derived() -> None:
    accepted = validate_bundle(CORPUS / "valid/l4-pass")
    rejected = validate_bundle(CORPUS / "valid/final-fail")
    assert accepted.gate_statuses["benefit_threshold"].status == "PASS"
    assert rejected.gate_statuses["benefit_threshold"].status == "FAIL"
    assert rejected.valid


def test_provenance_and_identity_are_content_addressed() -> None:
    report = validate_bundle(CORPUS / "valid/l5-pass")
    assert report.valid, report.as_dict()
    assert report.gate_statuses["provenance"].status == "PASS"
    assert "identity-generator" in report.evidence_graph["provenance-primary"]
    assert "identity-toolchain" in report.evidence_graph["provenance-primary"]


def test_repair_workflow_keeps_failed_candidate_immutable_and_reevaluates() -> None:
    bundle = ROOT / "examples/repair-workflow"
    repair = json.loads((bundle / "evidence/repair.json").read_text())
    manifest = json.loads((bundle / "manifest.json").read_text())
    assert repair["repair_count"] <= repair["maximum_repairs"]
    assert repair["result_reuse_across_source_hashes"] is False
    assert repair["full_reevaluation"] is True
    assert repair["failed_candidate_hash"] != manifest["machine"]["sha256"]
    assert validate_bundle(bundle).certification_eligible


def test_hash_mismatch_and_directory_substitution(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(ROOT / "examples/minimal", bundle)
    (bundle / "machine/generated.py").write_text("# MNCS-GENERATED\nchanged\n")
    report = validate_bundle(bundle)
    assert "hash-mismatch" in issue_codes(report)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["reference"] = {
        "path": "reference",
        "sha256": hash_path(bundle / "reference"),
    }
    manifest_path.write_text(json.dumps(manifest))
    report = validate_manifest(manifest_path)
    assert "invalid-evidence-type" in issue_codes(report)


def test_bundle_layout_is_required(tmp_path: Path) -> None:
    bundle = tmp_path / "empty"
    bundle.mkdir()
    report = validate_bundle(bundle)
    assert not report.valid
    assert "bundle-layout" in issue_codes(report)


def test_oversized_evidence_is_rejected_before_json_parsing(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(ROOT / "examples/minimal", bundle)
    (bundle / "evidence/gate-behavioral.json").write_bytes(b" " * (10 * 1024 * 1024 + 1))
    report = validate_bundle(bundle)
    assert not report.valid
    assert "unsafe-evidence" in issue_codes(report)
