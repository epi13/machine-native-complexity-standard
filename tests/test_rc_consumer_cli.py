"""General bounded Rust RC consumer CLI tests."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mncs_validator.assurance import validate_assurance_value
from mncs_validator.attestation import (
    attest,
    create_statement,
    generate_key,
    verify_attestation,
)
from mncs_validator.package import pack, verify_package
from mncs_validator.trust import evaluate

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "independent/rc-consumer/Cargo.toml"


def run_consumer(*args: str) -> tuple[int, dict[str, Any]]:
    process = subprocess.run(
        [
            "cargo",
            "run",
            "--quiet",
            "--manifest-path",
            str(MANIFEST),
            "--",
            *args,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return process.returncode, json.loads(process.stdout)


def test_general_record_cli_accepts_arbitrary_examples_and_offsets() -> None:
    status, contract = run_consumer(
        "validate-record",
        "--kind",
        "contract",
        "--input",
        "examples/release-candidate-0.3/contract-profile.json",
        "--json",
    )
    assert status == 0
    assert contract["category"] == "PASS"

    status, assurance = run_consumer(
        "validate-record",
        "--kind",
        "assurance",
        "--input",
        "examples/release-candidate-0.3/assurance-case.json",
        "--at",
        "2026-08-01T00:00:00-08:00",
        "--json",
    )
    assert status == 0
    assert assurance["category"] == "PASS"


def test_general_record_cli_rejects_invalid_and_reports_unsupported(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    status, result = run_consumer(
        "validate-record", "--kind", "contract", "--input", str(malformed), "--json"
    )
    assert status == 1
    assert result["category"] == "INVALID"

    record = tmp_path / "record.json"
    record.write_text("{}", encoding="utf-8")
    status, result = run_consumer(
        "validate-record", "--kind", "future-family", "--input", str(record), "--json"
    )
    assert status == 1
    assert result["category"] == "UNSUPPORTED"


def test_general_mncds_and_conformance_commands_preserve_boundaries() -> None:
    status, result = run_consumer(
        "validate-mncds",
        "--input",
        "examples/mncds-0.1-rc/development-record.json",
        "--json",
    )
    assert status == 0
    assert result["category"] == "UNKNOWN"

    status, result = run_consumer("conformance", "--json")
    assert status == 0
    assert result["category"] == "PASS"
    assert result["corpus"]["agreement"] >= 74
    assert result["implementation"]["independent_operation"] == "UNKNOWN"
    assert "general MNCS 0.2 package archive validation" not in result["unsupported_rules"]
    assert any("mncs-zip-0.1" in item for item in result["supported_rules"])


def test_mncds_reports_each_required_unknown_limitation(tmp_path: Path) -> None:
    value = json.loads(
        (ROOT / "examples/mncds-0.1-rc/development-record.json").read_text(encoding="utf-8")
    )
    value["release_controls"]["rollback"]["test_status"] = "UNKNOWN"
    path = tmp_path / "mncds-multiple-unknowns.json"
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    status, result = run_consumer("validate-mncds", "--input", str(path), "--json")
    assert status == 0
    assert result["category"] == "UNKNOWN"
    assert {"protected-evidence-unknown", "rollback-not-tested"} <= set(result["issue_codes"])


def test_independently_constructed_bounded_graph_fixtures_compare_exactly(
    tmp_path: Path,
) -> None:
    """Fixture construction shares neither consumer's decision implementation."""

    base = json.loads(
        (ROOT / "examples/release-candidate-0.3/assurance-case.json").read_text(encoding="utf-8")
    )
    complete = copy.deepcopy(base)
    complete["material_changes"] = [
        {
            "change_id": "change.generated-component-v2",
            "dimension": "artifact",
            "old_identity": "artifact.component-v1",
            "new_identity": "artifact.component-v2",
            "material": True,
            "rationale": "Independent fixture generator changed the required component.",
            "affected_claim_ids": ["claim.component"],
        }
    ]
    complete["evidence_impact"].update(
        {
            "affected_claim_ids": ["claim.component", "claim.system"],
            "invalidated_evidence_ids": ["evidence.component-v1"],
            "required_new_evidence_ids": ["evidence.component-v2"],
        }
    )
    complete["revalidation"].update(
        {
            "mode": "partial",
            "scope_claim_ids": ["claim.component", "claim.system"],
            "covered_change_ids": ["change.generated-component-v2"],
            "retained_evidence_ids": ["evidence.system-v1", "evidence.shared-v1"],
            "new_evidence_ids": ["evidence.component-v2"],
            "performed_at": "2026-08-01T00:00:00Z",
        }
    )
    incomplete = copy.deepcopy(complete)
    incomplete["evidence_impact"]["affected_claim_ids"] = ["claim.component"]
    incomplete["revalidation"]["scope_claim_ids"] = ["claim.component"]

    for name, value in (("complete", complete), ("incomplete", incomplete)):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
        python = validate_assurance_value(value, at=datetime(2026, 8, 1, tzinfo=UTC))
        _, rust = run_consumer(
            "validate-record",
            "--kind",
            "assurance",
            "--input",
            str(path),
            "--at",
            "2026-08-01T00:00:00Z",
            "--json",
        )
        assert rust["category"] == python.category
        assert set(rust["issue_codes"]) == {item.code for item in python.issues + python.warnings}


def test_rust_package_validation_matches_python_and_rejects_tampering(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "artifact.txt").write_text("bound artifact\n", encoding="utf-8")
    package = tmp_path / "valid.mncs"
    pack(bundle, package)

    python = verify_package(package)
    status, rust = run_consumer("validate-package", "--input", str(package), "--json")
    assert status == 0
    assert python.valid is True
    assert rust["category"] == "PASS"
    assert rust["report"]["package_sha256"] == python.package_sha256

    tampered = tmp_path / "tampered.mncs"
    with (
        zipfile.ZipFile(package) as source,
        zipfile.ZipFile(tampered, "x", compression=zipfile.ZIP_STORED) as target,
    ):
        for info in source.infolist():
            content = source.read(info.filename)
            if info.filename == "artifact.txt":
                content = b"evil! artifact\n"
            target.writestr(info, content)
    python = verify_package(tampered)
    status, rust = run_consumer("validate-package", "--input", str(tampered), "--json")
    assert status == 1
    assert python.valid is False
    assert rust["category"] == "INVALID"
    assert set(rust["issue_codes"]) == set(python.issues) == {"hash mismatch: artifact.txt"}


def test_rust_package_validation_rejects_traversal_and_symlink_members(
    tmp_path: Path,
) -> None:
    traversal = tmp_path / "traversal.mncs"
    with zipfile.ZipFile(traversal, "x", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("../escape", b"escape")
    status, result = run_consumer("validate-package", "--input", str(traversal), "--json")
    assert status == 1
    assert result["category"] == "INVALID"
    assert any("unsafe package path" in item for item in result["issue_codes"])

    symlink = tmp_path / "symlink.mncs"
    link = zipfile.ZipInfo("link")
    link.create_system = 3
    link.external_attr = 0o120777 << 16
    link.compress_type = zipfile.ZIP_STORED
    with zipfile.ZipFile(symlink, "x", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr(link, b"target")
    status, result = run_consumer("validate-package", "--input", str(symlink), "--json")
    assert status == 1
    assert result["category"] == "INVALID"
    assert any("unsafe archive member type" in item for item in result["issue_codes"])


def _attestation_fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    private = tmp_path / "private.pem"
    public = tmp_path / "public.json"
    generate_key(private, public)
    statement = create_statement(
        subjects=[
            {
                "name": "fixture",
                "digest": {"sha256": "a" * 64},
            }
        ],
        contract_id="fixture.contract",
        component={
            "name": "fixture-component",
            "version": "1.0.0",
            "identity": "sha256:" + "a" * 64,
        },
        environment="sha256:" + "b" * 64,
        predicate_type="https://mncs.dev/predicate/conformance-result/v0.2",
        predicate={"status": "PASS"},
        created_at="2026-01-01T00:00:00Z",
        expires_at="2030-01-01T00:00:00Z",
    )
    envelope = attest(statement, private)
    envelope_path = tmp_path / "envelope.json"
    envelope_path.write_text(json.dumps(envelope, sort_keys=True), encoding="utf-8")
    key = json.loads(public.read_text(encoding="utf-8"))
    key.update(
        {
            "trusted": True,
            "roles": ["evaluator"],
            "predicate_types": [statement["predicate_type"]],
            "components": ["fixture-component"],
            "contracts": ["fixture.contract"],
            "environments": [statement["environment"]],
            "valid_from": "2025-01-01T00:00:00Z",
            "valid_until": "2031-01-01T00:00:00Z",
        }
    )
    policy: dict[str, Any] = {
        "schema_version": "0.2",
        "trust_domain": "fixture.example",
        "keys": [key],
        "allowed_predicate_types": [statement["predicate_type"]],
        "minimum_signatures": 1,
        "distinct_signers": 1,
        "required_roles": ["evaluator"],
        "minimum_independent_evaluators": 1,
        "require_generator_evaluator_separation": False,
        "unknown_handling": "reject",
        "offline": True,
        "revocations": [],
        "extensions": {},
    }
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(policy, sort_keys=True), encoding="utf-8")
    return envelope_path, policy_path, policy


def test_rust_attestation_and_trust_policy_match_python(tmp_path: Path) -> None:
    envelope_path, policy_path, policy = _attestation_fixture(tmp_path)
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    moment = datetime(2026, 1, 1, tzinfo=UTC)
    python = evaluate(envelope, policy, now=moment)
    status, rust = run_consumer(
        "validate-attestation",
        "--envelope",
        str(envelope_path),
        "--policy",
        str(policy_path),
        "--at",
        "2026-01-01T00:00:00Z",
        "--subject",
        "sha256:" + "a" * 64,
        "--contract",
        "fixture.contract",
        "--environment",
        "sha256:" + "b" * 64,
        "--json",
    )
    assert status == 0
    assert python.certified is True
    assert rust["category"] == "PASS"
    assert rust["evaluation"]["certified"] is True
    assert rust["evaluation"]["trusted_signers"] == python.trusted_signers

    policy["revocations"] = [
        {
            "keyid": policy["keys"][0]["keyid"],
            "revoked_at": "2025-06-01T00:00:00Z",
            "reason": "fixture revocation",
            "extensions": {},
        }
    ]
    policy_path.write_text(json.dumps(policy, sort_keys=True), encoding="utf-8")
    python = evaluate(envelope, policy, now=moment)
    status, rust = run_consumer(
        "validate-attestation",
        "--envelope",
        str(envelope_path),
        "--policy",
        str(policy_path),
        "--at",
        "2026-01-01T00:00:00Z",
        "--json",
    )
    assert status == 0
    assert python.trusted is False
    assert rust["category"] == "FAIL"
    assert any("revoked key" in item for item in rust["issue_codes"])


def test_rust_attestation_rejects_invalid_binding_signature_and_time(
    tmp_path: Path,
) -> None:
    envelope_path, policy_path, policy = _attestation_fixture(tmp_path)
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    verification = verify_attestation(
        envelope,
        policy["keys"],
        expected_subject="sha256:" + "c" * 64,
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert verification.payload_valid is False
    status, rust = run_consumer(
        "validate-attestation",
        "--envelope",
        str(envelope_path),
        "--policy",
        str(policy_path),
        "--at",
        "2026-01-01T00:00:00Z",
        "--subject",
        "sha256:" + "c" * 64,
        "--json",
    )
    assert status == 1
    assert rust["category"] == "INVALID"
    assert "attestation subject binding mismatch" in rust["issue_codes"]

    envelope["signatures"][0]["sig"] = "A" * 88
    envelope_path.write_text(json.dumps(envelope, sort_keys=True), encoding="utf-8")
    status, rust = run_consumer(
        "validate-attestation",
        "--envelope",
        str(envelope_path),
        "--policy",
        str(policy_path),
        "--at",
        "2026-01-01T00:00:00Z",
        "--json",
    )
    assert status == 1
    assert rust["category"] == "INVALID"

    envelope_path, policy_path, _ = _attestation_fixture(tmp_path / "expired")
    status, rust = run_consumer(
        "validate-attestation",
        "--envelope",
        str(envelope_path),
        "--policy",
        str(policy_path),
        "--at",
        "2031-01-01T00:00:00Z",
        "--json",
    )
    assert status == 0
    assert rust["category"] == "FAIL"
    assert "attestation expired" in rust["issue_codes"]
