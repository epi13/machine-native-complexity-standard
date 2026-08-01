"""General bounded Rust RC consumer CLI tests."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mncs_validator.assurance import validate_assurance_value

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
    assert "general MNCS 0.2 package archive validation" in result["unsupported_rules"]


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
