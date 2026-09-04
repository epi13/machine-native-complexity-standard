# SPDX-License-Identifier: Apache-2.0

"""MNCS promotion boundary: schema, evaluator verdicts, and no-claim rules."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from mncs_validator.schemas import load_schema, schema_errors

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "scripts/mncs_promotion_evaluate.py"
BOUNDARY_EXAMPLE = ROOT / "examples/promotion-boundary/family-promotion.boundary.json"

REPO = "epi13/mncs-actions"
COMMIT = "a" * 40
OTHER_COMMIT = "b" * 40

AUTHORITIES = {
    "mncs-validation": "machine-native-complexity-standard",
    "mncds-development-record": "machine-native-complexity-development-specification",
    "mncds-obligations": "machine-native-complexity-development-specification",
    "forge-cell-contract": "mncs-forge-mcp",
}

CONTRACTS = {
    "mncs-validation": "0.2",
    "mncds-development-record": "0.2-alpha.1",
    "mncds-obligations": "mncds-obligation-record/0.1",
}


def _authority_map_doc() -> dict[str, object]:
    return {
        "schema_version": "mncs-authority-map/0.1",
        "authorities": {
            check_id: {"provider": f"provider-for-{check_id}", "authority": authority}
            for check_id, authority in AUTHORITIES.items()
        },
    }


def _boundary_doc() -> dict[str, Any]:
    return json.loads(BOUNDARY_EXAMPLE.read_text(encoding="utf-8"))


def _check(
    check_id: str,
    verdict: str,
    *,
    commit: str = COMMIT,
    contract_revision: str | None = None,
    unresolved: list[str] | None = None,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "schema_version": "mncs.check-result/1",
        "id": check_id,
        "provider": f"provider-for-{check_id}",
        "verdict": verdict,
        "subject": {"repository": REPO, "commit": commit},
    }
    if contract_revision is not None:
        doc["contract_revision"] = contract_revision
    if unresolved is not None:
        doc["unresolved"] = unresolved
    return doc


def _obligation(
    key: str,
    status: str,
    *,
    required: bool = True,
    commit: str = COMMIT,
    resolution: str | None = None,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "schema_version": "mncds-obligation-record/0.2",
        "obligation_key": key,
        "status": status,
        "required": required,
        "subject": {"repository": REPO, "commit": commit},
        "origin": {"kind": "development-pressure", "authority": "mncs-actions"},
        "evidence": [],
        "supersedes": None,
        "extensions": {},
    }
    if status in ("resolved", "rejected"):
        doc["resolution"] = {
            "resolution": resolution or ("fixed" if status == "resolved" else "rejected"),
            "evidence_refs": ["sha256:" + "c" * 64],
            "resolved_by": "epi13/mncs-actions",
            "resolved_at": "2026-09-04T00:00:00Z",
        }
    return doc


def _run(
    tmp_path: Path,
    boundary: dict[str, Any],
    checks: list[dict[str, Any]],
    obligations: list[dict[str, Any]],
    *,
    commit: str = COMMIT,
    repository: str = REPO,
    authority_map: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | None, str]:
    boundary_path = tmp_path / "boundary.json"
    boundary_path.write_text(json.dumps(boundary), encoding="utf-8")
    map_path = tmp_path / "authority-map.json"
    map_path.write_text(
        json.dumps(authority_map if authority_map is not None else _authority_map_doc()),
        encoding="utf-8",
    )
    check_paths = []
    for index, check in enumerate(checks):
        path = tmp_path / f"check-{index}.json"
        path.write_text(json.dumps(check), encoding="utf-8")
        check_paths.append(str(path))
    obligation_paths = []
    for index, record in enumerate(obligations):
        path = tmp_path / f"obligation-{index}.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        obligation_paths.append(str(path))
    output = tmp_path / "promotion.json"
    command = [
        sys.executable,
        str(EVALUATOR),
        "--boundary",
        str(boundary_path),
        "--authority-map",
        str(map_path),
        "--subject-repository",
        repository,
        "--subject-commit",
        commit,
        "--output",
        str(output),
    ]
    if check_paths:
        command += ["--checks", *check_paths]
    if obligation_paths:
        command += ["--obligations", *obligation_paths]
    process = subprocess.run(command, capture_output=True, text=True, timeout=60)
    result = None
    if output.is_file():
        result = json.loads(output.read_text(encoding="utf-8"))
    return process.returncode, result, process.stderr


def _required_pass_set() -> list[dict[str, Any]]:
    return [
        _check("mncs-validation", "PASS", contract_revision="0.2"),
        _check("mncds-development-record", "PASS", contract_revision="0.2-alpha.1"),
        _check(
            "mncds-obligations",
            "PASS",
            contract_revision="mncds-obligation-record/0.1",
        ),
    ]


def test_boundary_example_is_schema_valid() -> None:
    schema = load_schema("promotion-boundary-0.1")
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema_errors(_boundary_doc(), "promotion-boundary-0.1") == []


def test_authority_map_example_is_schema_valid() -> None:
    path = BOUNDARY_EXAMPLE.parent / "family-authority-map.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert schema_errors(doc, "authority-map-0.1") == []
    assert set(doc["authorities"]) >= {
        "mncs-validation",
        "mncds-development-record",
        "mncds-obligations",
    }


def test_all_required_pass_promotes(tmp_path: Path) -> None:
    code, result, _ = _run(tmp_path, _boundary_doc(), _required_pass_set(), [])
    assert code == 0
    assert result is not None and result["verdict"] == "PASS"
    assert result["id"] == "promotion-boundary"
    assert result["promotion"]["blockers"] == []
    assert result["subject"] == {"repository": REPO, "commit": COMMIT}
    digests = [ref["digest"] for ref in result["references"]]
    assert digests and all(d.startswith("sha256:") for d in digests)


def test_required_fail_blocks(tmp_path: Path) -> None:
    checks = _required_pass_set()
    checks[0] = _check("mncs-validation", "FAIL", contract_revision=CONTRACTS["mncs-validation"])
    code, result, _ = _run(tmp_path, _boundary_doc(), checks, [])
    assert code == 0
    assert result is not None and result["verdict"] == "FAIL"
    assert any("mncs-validation" in item for item in result["promotion"]["blockers"])


def test_missing_required_is_unknown_not_pass(tmp_path: Path) -> None:
    checks = [c for c in _required_pass_set() if c["id"] != "mncds-obligations"]
    code, result, _ = _run(tmp_path, _boundary_doc(), checks, [])
    assert code == 0
    assert result is not None and result["verdict"] == "UNKNOWN"
    assert any("mncds-obligations" in item for item in result["promotion"]["blockers"])


def test_required_unknown_is_unknown(tmp_path: Path) -> None:
    checks = _required_pass_set()
    checks[1] = _check(
        "mncds-development-record",
        "UNKNOWN",
        contract_revision="0.2-alpha.1",
        unresolved=["record valid; selection pending"],
    )
    code, result, _ = _run(tmp_path, _boundary_doc(), checks, [])
    assert code == 0
    assert result is not None and result["verdict"] == "UNKNOWN"


def test_open_required_obligation_blocks_with_key(tmp_path: Path) -> None:
    code, result, _ = _run(
        tmp_path,
        _boundary_doc(),
        _required_pass_set(),
        [_obligation("pressure.gap-1", "open")],
    )
    assert code == 0
    assert result is not None and result["verdict"] == "UNKNOWN"
    assert any("pressure.gap-1" in item for item in result["promotion"]["blockers"])


def test_tolerated_obligation_does_not_block(tmp_path: Path) -> None:
    boundary = _boundary_doc()
    boundary["tolerated_obligations"] = ["pressure.gap-1"]
    code, result, _ = _run(
        tmp_path, boundary, _required_pass_set(), [_obligation("pressure.gap-1", "open")]
    )
    assert code == 0
    assert result is not None and result["verdict"] == "PASS"


def test_optional_fail_stays_visible_without_deciding(tmp_path: Path) -> None:
    checks = [*_required_pass_set(), _check("forge-cell-contract", "FAIL")]
    code, result, _ = _run(tmp_path, _boundary_doc(), checks, [])
    assert code == 0
    assert result is not None and result["verdict"] == "PASS"
    assert any("forge-cell-contract" in item for item in result.get("unresolved", []))


def test_missing_optional_has_no_effect(tmp_path: Path) -> None:
    code, result, _ = _run(tmp_path, _boundary_doc(), _required_pass_set(), [])
    assert code == 0
    assert result is not None and result["verdict"] == "PASS"


def test_rejected_obligation_is_negative(tmp_path: Path) -> None:
    code, result, _ = _run(
        tmp_path,
        _boundary_doc(),
        _required_pass_set(),
        [_obligation("pressure.gap-9", "rejected")],
    )
    assert code == 0
    assert result is not None and result["verdict"] == "FAIL"


def test_wrong_revision_stamp_establishes_no_claim(tmp_path: Path) -> None:
    checks = _required_pass_set()
    checks[0] = _check("mncs-validation", "PASS", commit=OTHER_COMMIT)
    code, result, stderr = _run(tmp_path, _boundary_doc(), checks, [])
    assert code == 2
    assert result is None
    assert "stamped" in stderr


def test_obligation_for_other_subject_establishes_no_claim(tmp_path: Path) -> None:
    code, result, _ = _run(
        tmp_path,
        _boundary_doc(),
        _required_pass_set(),
        [_obligation("pressure.gap-1", "open", commit=OTHER_COMMIT)],
    )
    assert code == 2
    assert result is None


def test_moving_subject_establishes_no_claim(tmp_path: Path) -> None:
    code, result, _ = _run(tmp_path, _boundary_doc(), _required_pass_set(), [], commit="main")
    assert code == 2
    assert result is None


def test_duplicate_check_ids_establish_no_claim(tmp_path: Path) -> None:
    checks = [*_required_pass_set(), _check("mncs-validation", "PASS")]
    code, result, _ = _run(tmp_path, _boundary_doc(), checks, [])
    assert code == 2
    assert result is None


def test_malformed_check_establishes_no_claim(tmp_path: Path) -> None:
    bad = _check("mncs-validation", "PASS")
    bad["verdict"] = "FORGED"
    code, result, _ = _run(tmp_path, _boundary_doc(), [bad], [])
    assert code == 2
    assert result is None


def test_contract_mismatch_is_unknown_not_fail(tmp_path: Path) -> None:
    checks = _required_pass_set()
    checks[0] = _check("mncs-validation", "PASS", contract_revision="9.9")
    code, result, _ = _run(tmp_path, _boundary_doc(), checks, [])
    assert code == 0
    assert result is not None and result["verdict"] == "UNKNOWN"


def test_forged_provider_with_correct_id_establishes_no_claim(tmp_path: Path) -> None:
    checks = _required_pass_set()
    forged = _check("mncs-validation", "PASS", contract_revision=CONTRACTS["mncs-validation"])
    forged["provider"] = "attacker-provider"
    checks[0] = forged
    code, result, stderr = _run(tmp_path, _boundary_doc(), checks, [])
    assert code == 2
    assert result is None
    assert "not the bound" in stderr


def test_wrong_reference_authority_establishes_no_claim(tmp_path: Path) -> None:
    checks = _required_pass_set()
    checks[0]["references"] = [
        {
            "kind": "check-result",
            "authority": "attacker-authority",
            "digest": "sha256:" + "d" * 64,
        }
    ]
    code, result, _ = _run(tmp_path, _boundary_doc(), checks, [])
    assert code == 2
    assert result is None


def test_missing_authority_binding_is_unknown_not_pass(tmp_path: Path) -> None:
    narrowed = {
        "schema_version": "mncs-authority-map/0.1",
        "authorities": {
            check_id: binding
            for check_id, binding in _authority_map_doc()["authorities"].items()
            if check_id != "mncds-obligations"
        },
    }
    code, result, _ = _run(
        tmp_path, _boundary_doc(), _required_pass_set(), [], authority_map=narrowed
    )
    assert code == 0
    assert result is not None and result["verdict"] == "UNKNOWN"
    assert any("no authority binding" in item for item in result["promotion"]["blockers"])


def test_missing_contract_revision_is_unknown_not_pass(tmp_path: Path) -> None:
    checks = _required_pass_set()
    checks[1] = _check("mncds-development-record", "PASS")
    code, result, _ = _run(tmp_path, _boundary_doc(), checks, [])
    assert code == 0
    assert result is not None and result["verdict"] == "UNKNOWN"
    assert any("does not establish" in item for item in result["promotion"]["blockers"])


def test_malformed_contract_revision_establishes_no_claim(tmp_path: Path) -> None:
    checks = _required_pass_set()
    checks[1]["contract_revision"] = {"spoofed": True}
    code, result, _ = _run(tmp_path, _boundary_doc(), checks, [])
    assert code == 2
    assert result is None


def test_optional_wrong_authority_is_visible_not_deciding(tmp_path: Path) -> None:
    checks = [
        *_required_pass_set(),
        _check("forge-cell-contract", "FAIL", contract_revision="0.1"),
    ]
    narrowed = {
        "schema_version": "mncs-authority-map/0.1",
        "authorities": {
            check_id: binding
            for check_id, binding in _authority_map_doc()["authorities"].items()
            if check_id != "forge-cell-contract"
        },
    }
    code, result, _ = _run(tmp_path, _boundary_doc(), checks, [], authority_map=narrowed)
    assert code == 0
    assert result is not None and result["verdict"] == "PASS"
    assert any("forge-cell-contract" in item for item in result.get("unresolved", []))


def test_obligation_evidence_is_digest_bound(tmp_path: Path) -> None:
    first = _obligation("pressure.gap-1", "resolved")
    code, result, _ = _run(tmp_path, _boundary_doc(), _required_pass_set(), [first])
    assert code == 0
    assert result is not None and result["verdict"] == "PASS"
    obligation_refs = [
        ref for ref in result["references"] if ref["kind"] == "mncds-obligation-record"
    ]
    assert len(obligation_refs) == 1
    ref = obligation_refs[0]
    assert ref["obligation_key"] == "pressure.gap-1"
    assert ref["digest"].startswith("sha256:")
    assert ref["subject"] == {"repository": REPO, "commit": COMMIT}
    assert ref["status"] == "resolved"
    # Changing one obligation byte changes the bound digest.
    second = _obligation("pressure.gap-1", "resolved")
    second["evidence"] = ["different evidence"]
    code, result2, _ = _run(tmp_path, _boundary_doc(), _required_pass_set(), [second])
    assert code == 0
    assert result2 is not None
    ref2 = next(item for item in result2["references"] if item["kind"] == "mncds-obligation-record")
    assert ref2["digest"] != ref["digest"]


def test_anonymous_resolution_establishes_no_claim(tmp_path: Path) -> None:
    record = _obligation("pressure.gap-1", "resolved")
    del record["resolution"]["resolved_by"]
    code, result, _ = _run(tmp_path, _boundary_doc(), _required_pass_set(), [record])
    assert code == 2
    assert result is None


def test_incoherent_resolution_kind_establishes_no_claim(tmp_path: Path) -> None:
    record = _obligation("pressure.gap-1", "resolved", resolution="rejected")
    code, result, _ = _run(tmp_path, _boundary_doc(), _required_pass_set(), [record])
    assert code == 2
    assert result is None


def test_self_referential_output_is_noted_not_blocking(tmp_path: Path) -> None:
    boundary = _boundary_doc()
    boundary["required_evidence"] = [
        *boundary["required_evidence"],
        {"check_id": "promotion-boundary", "authority": "machine-native-complexity-standard"},
    ]
    code, result, _ = _run(tmp_path, boundary, _required_pass_set(), [])
    assert code == 0
    assert result is not None and result["verdict"] == "PASS"
    assert result["promotion"]["required_total"] == 3
    assert result["promotion"]["required_passed"] == 3
    assert any("own output" in item for item in result.get("unresolved", []))


def test_conflicting_check_revisions_are_unknown(tmp_path: Path) -> None:
    checks = _required_pass_set()
    checks[1] = _check("mncds-development-record", "PASS", contract_revision="0.1-rc.1")
    checks[2] = _check("mncds-obligations", "PASS", contract_revision="mncds-obligation-record/9.9")
    code, result, _ = _run(tmp_path, _boundary_doc(), checks, [])
    assert code == 0
    assert result is not None and result["verdict"] == "UNKNOWN"
    assert len([item for item in result["promotion"]["blockers"] if "mismatch" in item]) == 2
