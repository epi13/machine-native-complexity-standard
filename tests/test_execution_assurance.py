# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mncs_validator.assurance import validate_rc_file
from mncs_validator.canonical import canonical_sha256_file
from mncs_validator.execution_assurance import validate_execution_assurance_value
from mncs_validator.execution_assurance_cli import mncds_main, mncs_main
from mncs_validator.mncds import validate_development_record
from mncs_validator.schemas import load_schema

ROOT = Path(__file__).resolve().parents[1]
AT = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
AT_TEXT = "2026-07-28T12:00:00Z"

BASIC_REQUIRED = [
    "command_bound",
    "environment_bound",
    "filesystem_isolation",
    "network_isolation",
    "process_isolation",
    "resource_limits",
    "test_integrity",
    "result_integrity",
]


def _record(
    subject: Path,
    *,
    family: str,
    kind: str,
    test_status: str,
    attestation_kind: str = "none",
    required_properties: list[str] | None = None,
) -> dict[str, Any]:
    properties = {
        "command_bound": "PASS",
        "environment_bound": "PASS",
        "filesystem_isolation": "PASS",
        "network_isolation": "PASS",
        "process_isolation": "PASS",
        "resource_limits": "PASS",
        "test_integrity": "PASS",
        "result_integrity": "PASS",
        "host_root_resistance": "UNKNOWN",
        "protected_custody": "UNKNOWN",
        "independent_operation": "UNKNOWN",
    }
    if attestation_kind == "none":
        attestation = {
            "kind": "none",
            "identity": None,
            "signer_id": None,
            "verified": False,
            "fresh": True,
        }
        declared = "UNKNOWN"
    else:
        attestation = {
            "kind": attestation_kind,
            "identity": "e" * 64,
            "signer_id": "evaluator.example",
            "verified": True,
            "fresh": True,
        }
        declared = "PASS"
    return {
        "schema_version": "0.1",
        "record_type": "mncs-execution-assurance",
        "record_id": f"execution.{family.lower()}.example-v1",
        "subject": {
            "family": family,
            "kind": kind,
            "record_id": f"subject.{family.lower()}.example-v1",
            "canonical_sha256": canonical_sha256_file(subject),
            "candidate_id": "candidate.example-v1",
        },
        "test_result": {
            "status": test_status,
            "result_identity": "b" * 64,
            "summary": "The bound offline subject validator completed.",
        },
        "execution": {
            "test_bundle_identity": "c" * 64,
            "policy_identity": "d" * 64,
            "runner_identity": "runner.example-v1",
            "environment_identity": "environment.example-v1",
            "challenge": {
                "nonce": "challenge-0123456789abcdef",
                "issued_at": "2026-07-28T00:00:00Z",
                "expires_at": "2026-07-29T00:00:00Z",
            },
            "properties": properties,
            "attestation": attestation,
        },
        "required_properties": required_properties or list(BASIC_REQUIRED),
        "declared_assurance_status": declared,
        "limitations": [
            "This fixture does not claim more authority than its attestation kind supports."
        ],
        "extensions": {},
    }


def _write(path: Path, value: dict[str, Any]) -> Path:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return path


def test_schema_is_packaged() -> None:
    schema = load_schema("execution-assurance-0.1")
    assert schema["title"] == "MNCS/MNCDS execution assurance record 0.1"


def test_test_pass_remains_unknown_without_attestation() -> None:
    subject = ROOT / "examples/release-candidate-0.3/measurement-profile.json"
    value = _record(subject, family="MNCS", kind="measurement", test_status="PASS")
    report = validate_execution_assurance_value(value, subject_path=subject, at=AT)
    assert report.valid
    assert report.test_status == "PASS"
    assert report.assurance_status == "UNKNOWN"
    assert report.combined_status == "UNKNOWN"
    assert {item.code for item in report.warnings} == {"attestation-absent"}


def test_signed_local_can_pass_basic_isolation_but_not_host_root_resistance() -> None:
    subject = ROOT / "examples/release-candidate-0.3/measurement-profile.json"
    value = _record(
        subject,
        family="MNCS",
        kind="measurement",
        test_status="PASS",
        attestation_kind="signed-local",
    )
    report = validate_execution_assurance_value(value, subject_path=subject, at=AT)
    assert report.category == "PASS"
    assert report.property_results["host_root_resistance"] == "UNKNOWN"


def test_local_attestation_cannot_overclaim_host_root_resistance() -> None:
    subject = ROOT / "examples/release-candidate-0.3/measurement-profile.json"
    value = _record(
        subject,
        family="MNCS",
        kind="measurement",
        test_status="PASS",
        attestation_kind="signed-local",
        required_properties=[*BASIC_REQUIRED, "host_root_resistance"],
    )
    value["execution"]["properties"]["host_root_resistance"] = "PASS"
    report = validate_execution_assurance_value(value, subject_path=subject, at=AT)
    assert report.category == "INVALID"
    assert any(item.code == "local-attestation-overclaim" for item in report.warnings)
    assert any(item.code == "assurance-status-mismatch" for item in report.issues)


def test_external_evaluator_can_satisfy_explicit_high_assurance_properties() -> None:
    subject = ROOT / "examples/release-candidate-0.3/measurement-profile.json"
    required = [
        *BASIC_REQUIRED,
        "host_root_resistance",
        "protected_custody",
        "independent_operation",
    ]
    value = _record(
        subject,
        family="MNCS",
        kind="measurement",
        test_status="PASS",
        attestation_kind="external-evaluator",
        required_properties=required,
    )
    for name in required:
        value["execution"]["properties"][name] = "PASS"
    report = validate_execution_assurance_value(value, subject_path=subject, at=AT)
    assert report.category == "PASS"


def test_subject_substitution_and_challenge_replay_fail_closed() -> None:
    subject = ROOT / "examples/release-candidate-0.3/measurement-profile.json"
    value = _record(
        subject,
        family="MNCS",
        kind="measurement",
        test_status="PASS",
        attestation_kind="signed-local",
    )
    substituted = deepcopy(value)
    substituted["subject"]["canonical_sha256"] = "0" * 64
    mismatch = validate_execution_assurance_value(substituted, subject_path=subject, at=AT)
    assert mismatch.category == "FAIL"
    assert any(item.code == "subject-identity-mismatch" for item in mismatch.warnings)

    expired = validate_execution_assurance_value(
        value,
        subject_path=subject,
        at=datetime(2026, 7, 30, tzinfo=UTC),
    )
    assert expired.category == "FAIL"
    assert any(item.code == "challenge-expired" for item in expired.warnings)


def test_unsupported_execution_schema_remains_unsupported() -> None:
    subject = ROOT / "examples/release-candidate-0.3/measurement-profile.json"
    value = _record(subject, family="MNCS", kind="measurement", test_status="PASS")
    value["schema_version"] = "9.9"
    report = validate_execution_assurance_value(value, at=AT)
    assert report.category == "UNSUPPORTED"
    assert not report.supported


def test_mncs_combined_cli_requires_subject_and_execution_assurance_pass(
    tmp_path: Path,
    capsys: object,
) -> None:
    subject = ROOT / "examples/release-candidate-0.3/measurement-profile.json"
    subject_report = validate_rc_file(subject, "measurement", at=AT)
    assurance = _write(
        tmp_path / "mncs-execution.json",
        _record(
            subject,
            family="MNCS",
            kind="measurement",
            test_status=subject_report.computed_status,
        ),
    )
    assert (
        mncs_main(
            [
                "validate",
                "measurement",
                str(subject),
                str(assurance),
                "--at",
                AT_TEXT,
                "--require-pass",
                "--json",
            ]
        )
        == 3
    )
    value = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert value["subject"]["category"] == "PASS"
    assert value["execution_assurance"]["assurance_status"] == "UNKNOWN"
    assert value["category"] == "UNKNOWN"


def test_mncds_combined_cli_uses_same_execution_assurance_rules(
    tmp_path: Path,
    capsys: object,
) -> None:
    subject = ROOT / "examples/mncds-0.1-rc/development-record.json"
    subject_report = validate_development_record(subject)
    assurance = _write(
        tmp_path / "mncds-execution.json",
        _record(
            subject,
            family="MNCDS",
            kind="development-record",
            test_status=subject_report.computed_status,
        ),
    )
    expected = "FAIL" if subject_report.computed_status == "FAIL" else "UNKNOWN"
    assert (
        mncds_main(
            [
                "validate",
                str(subject),
                str(assurance),
                "--at",
                AT_TEXT,
                "--require-pass",
                "--json",
            ]
        )
        == 3
    )
    value = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert value["execution_assurance"]["assurance_status"] == "UNKNOWN"
    assert value["category"] == expected
