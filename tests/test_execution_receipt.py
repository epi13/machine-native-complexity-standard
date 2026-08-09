from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mncs_validator.canonical import canonical_sha256
from mncs_validator.cli import main
from mncs_validator.execution_assurance import validate_execution_assurance_value
from mncs_validator.execution_receipt import (
    validate_execution_receipt_binding,
    validate_execution_receipt_value,
)
from mncs_validator.schemas import load_schema

ROOT = Path(__file__).resolve().parents[1]


def _receipt(*, termination: str = "completed") -> dict[str, Any]:
    exit_code = 0 if termination == "completed" else 17
    signal = None
    timeout = None
    resource = None
    if termination == "timeout":
        exit_code = None
        timeout = 5.0
    elif termination in {"signal", "crash"}:
        exit_code = None
        signal = 9
    elif termination == "resource-limit":
        exit_code = None
        resource = "host-memory"
    elif termination == "output-limit":
        exit_code = None
    value: dict[str, Any] = {
        "schema_version": "0.1-experimental",
        "record_type": "mncs-execution-receipt",
        "record_id": "receipt.local.example-v1",
        "receipt_identity": "0" * 64,
        "subject": {
            "family": "MNCS",
            "kind": "measurement",
            "record_id": "subject.measurement.example-v1",
            "canonical_sha256": "a" * 64,
            "candidate_id": "candidate.example-v1",
        },
        "bundle": {
            "test_bundle_identity": "b" * 64,
            "harness_identity": "c" * 64,
            "input_snapshot_identity": None,
        },
        "policy": {
            "execution_policy_identity": "d" * 64,
            "placement_policy_identity": None,
            "requested_limits": [
                {"resource": "timeout", "value": 30, "unit": "seconds"},
                {"resource": "output", "value": 1024, "unit": "bytes"},
            ],
            "result_semantics": "harness result is independent from runner assurance",
        },
        "runner": {
            "runner_identity": "runner.local.example-v1",
            "runner_version": "1.0.0",
            "executable_identity": "e" * 64,
            "runtime_identity": "runtime.python.example-v1",
            "command_identity": "f" * 64,
        },
        "environment": {"environment_identity": "environment.local.example-v1"},
        "challenge": {
            "nonce": "challenge-0123456789abcdef",
            "issued_at": "2026-08-08T00:00:00Z",
            "expires_at": "2026-08-08T01:00:00Z",
        },
        "request": {"status": "accepted", "observed_at": "2026-08-08T00:00:01Z"},
        "lifecycle": {
            "started_at": "2026-08-08T00:00:02Z",
            "ended_at": "2026-08-08T00:00:03Z",
            "duration_seconds": 1,
            "termination_category": termination,
        },
        "process": {
            "exit_code": exit_code,
            "signal": signal,
            "harness_status": "PASS" if termination == "completed" else "FAIL",
            "result_identity": "1" * 64,
        },
        "termination_observations": {"timeout_seconds": timeout, "resource_name": resource},
        "streams": {
            "stdout": {
                "total_bytes": 5,
                "retained_bytes": 5,
                "retained_sha256": "2" * 64,
                "complete_sha256": "3" * 64,
                "truncated": False,
                "limit_hit": termination == "output-limit",
                "limit_bytes": 5 if termination == "output-limit" else None,
            },
            "stderr": {
                "total_bytes": 0,
                "retained_bytes": 0,
                "retained_sha256": None,
                "complete_sha256": None,
                "truncated": False,
                "limit_hit": False,
                "limit_bytes": None,
            },
        },
        "aggregate_output": {
            "total_bytes": 5,
            "retained_bytes": 5,
            "limit_bytes": 5 if termination == "output-limit" else None,
            "limit_hit": termination == "output-limit",
        },
        "artifacts": [{"identity": "1" * 64, "kind": "result", "size_bytes": 12, "retained": True}],
        "resources": [
            {
                "metric": "wall-duration",
                "value": 1,
                "unit": "seconds",
                "source_identity": "source.clock-v1",
                "phase": "whole-execution",
            },
            {
                "metric": "process-rss-peak",
                "value": 4096,
                "unit": "bytes",
                "source_identity": "source.proc-v1",
                "phase": "whole-execution",
            },
        ],
        "enforcement": {
            "command_binding": "enforced",
            "environment_binding": "enforced",
            "filesystem_restriction": "unknown",
            "network_restriction": "unknown",
            "process_restriction": "unknown",
            "resource_limits": "enforced",
            "test_bundle_integrity": "enforced",
            "result_integrity": "enforced",
        },
        "placement": {"execution_placement_reference": None},
        "claim_boundary": {
            "conformance": "not-asserted",
            "correctness": "not-asserted",
            "security": "not-asserted",
            "sandbox": "not-asserted",
            "independence": "not-asserted",
            "protected_custody": "not-asserted",
            "promotion": "not-asserted",
        },
        "extensions": {},
    }
    value["receipt_identity"] = canonical_sha256(
        {k: v for k, v in value.items() if k != "receipt_identity"}
    )
    return value


def _assurance(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "record_type": "mncs-execution-assurance",
        "record_id": "assurance.example-v1",
        "subject": copy.deepcopy(value["subject"]),
        "test_result": {"status": "PASS", "result_identity": "1" * 64, "summary": "bounded result"},
        "execution": {
            "test_bundle_identity": value["bundle"]["test_bundle_identity"],
            "policy_identity": value["policy"]["execution_policy_identity"],
            "runner_identity": value["runner"]["runner_identity"],
            "environment_identity": value["environment"]["environment_identity"],
            "challenge": copy.deepcopy(value["challenge"]),
            "properties": {
                "command_bound": "PASS",
                "environment_bound": "UNKNOWN",
                "filesystem_isolation": "UNKNOWN",
                "network_isolation": "UNKNOWN",
                "process_isolation": "UNKNOWN",
                "resource_limits": "PASS",
                "test_integrity": "PASS",
                "result_integrity": "PASS",
                "host_root_resistance": "UNKNOWN",
                "protected_custody": "UNKNOWN",
                "independent_operation": "UNKNOWN",
            },
            "attestation": {
                "kind": "none",
                "identity": None,
                "signer_id": None,
                "verified": False,
                "fresh": True,
            },
        },
        "execution_receipt": {
            "record_id": value["record_id"],
            "identity": value["receipt_identity"],
        },
        "required_properties": [
            "command_bound",
            "resource_limits",
            "test_integrity",
            "result_integrity",
        ],
        "declared_assurance_status": "UNKNOWN",
        "limitations": ["Local runner observations do not establish custody or independence."],
        "extensions": {},
    }


def test_schema_and_canonical_identity_are_packaged() -> None:
    schema = load_schema("execution-receipt-0.1-experimental")
    assert schema["title"] == "MNCS experimental typed execution receipt 0.1"
    value = _receipt()
    assert validate_execution_receipt_value(value).category == "PASS"
    assert validate_execution_receipt_value(value).receipt_identity == value["receipt_identity"]
    assert (
        validate_execution_receipt_value(copy.deepcopy(value)).receipt_identity
        == value["receipt_identity"]
    )


def test_reference_fixture_and_corpus_index() -> None:
    fixture = json.loads(
        (
            ROOT / "experimental/execution-receipt/fixtures/valid/generic-local-runner.json"
        ).read_text()
    )
    assert validate_execution_receipt_value(fixture).category == "PASS"
    index = json.loads(
        (ROOT / "experimental/execution-receipt/fixtures/corpus-index.json").read_text()
    )
    assert len(index["cases"]) >= 40
    assert {case["expected"] for case in index["cases"]} >= {
        "PASS",
        "INVALID",
        "UNKNOWN",
        "UNSUPPORTED",
    }


def test_execution_placement_reference_can_be_resolved() -> None:
    placement = json.loads(
        (
            ROOT / "experimental/execution-placement/fixtures/valid/sequential-offload.json"
        ).read_text()
    )
    value = _receipt()
    value["environment"]["environment_identity"] = placement["identities"]["environment_id"]
    value["placement"]["execution_placement_reference"] = {
        "record_id": placement["record_id"],
        "identity": canonical_sha256(placement),
        "subject_identity": value["subject"]["canonical_sha256"],
        "environment_identity": value["environment"]["environment_identity"],
    }
    value["receipt_identity"] = canonical_sha256(
        {key: child for key, child in value.items() if key != "receipt_identity"}
    )
    report = validate_execution_receipt_value(value, placement_value=placement)
    assert report.category == "PASS"


def test_process_failures_are_valid_observations_not_conformance_verdicts() -> None:
    for termination in ("nonzero-exit", "timeout", "crash", "resource-limit", "output-limit"):
        report = validate_execution_receipt_value(_receipt(termination=termination))
        assert report.valid, termination
        assert report.execution_status == "FAIL"
        assert report.category == "PASS", termination


def test_adversarial_receipt_facts_fail_closed() -> None:
    mutations = []
    value = _receipt()
    mutated = copy.deepcopy(value)
    mutated["receipt_identity"] = "9" * 64
    mutations.append(mutated)
    mutated = copy.deepcopy(value)
    mutated["streams"]["stdout"]["retained_bytes"] = 6
    mutated["receipt_identity"] = canonical_sha256(
        {k: v for k, v in mutated.items() if k != "receipt_identity"}
    )
    mutations.append(mutated)
    mutated = copy.deepcopy(value)
    mutated["lifecycle"]["termination_category"] = "timeout"
    mutated["termination_observations"]["timeout_seconds"] = None
    mutated["receipt_identity"] = canonical_sha256(
        {k: v for k, v in mutated.items() if k != "receipt_identity"}
    )
    mutations.append(mutated)
    mutated = copy.deepcopy(value)
    mutated["resources"][0]["unit"] = "bytes"
    mutated["receipt_identity"] = canonical_sha256(
        {k: v for k, v in mutated.items() if k != "receipt_identity"}
    )
    mutations.append(mutated)
    assert all(not validate_execution_receipt_value(item).valid for item in mutations)


def test_receipt_assurance_binding_rejects_substitution_and_overclaim() -> None:
    value = _receipt()
    assurance = _assurance(value)
    assert validate_execution_receipt_binding(assurance, value).valid
    substituted = copy.deepcopy(assurance)
    substituted["subject"]["record_id"] = "subject.other-v1"
    assert not validate_execution_receipt_binding(substituted, value).valid
    overclaim = copy.deepcopy(assurance)
    overclaim["execution"]["properties"]["filesystem_isolation"] = "PASS"
    assert not validate_execution_receipt_binding(overclaim, value).valid


def test_execution_assurance_schema_accepts_optional_receipt_reference() -> None:
    value = _receipt()
    assurance = _assurance(value)
    report = validate_execution_assurance_value(
        assurance, at=datetime(2026, 8, 8, 0, 30, tzinfo=UTC)
    )
    assert report.valid


def test_receipt_cli(tmp_path: Path, capsys: object) -> None:
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(_receipt(), indent=2) + "\n", encoding="utf-8")
    assert main(["schema", "execution-receipt-0.1-experimental", "--json"]) == 0
    capsys.readouterr()  # type: ignore[attr-defined]
    assert main(["validate-execution-receipt", str(path), "--json", "--require-pass"]) == 0
    result = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert result["category"] == "PASS"
    assert result["execution_status"] == "PASS"
