# SPDX-License-Identifier: Apache-2.0

"""Repository-owned promotion adoption coherence (offline).

Pins the relationships between the files MNCS owns for promotion: the
candidate revision, the boundary's required evidence, the authority map,
and the obligation set. Evaluator behavior and transport claims are
covered by scripts/assert-promotion-vectors.sh in CI.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMOTION = ROOT / "promotion"
HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")

REPO = "epi13/machine-native-complexity-standard"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_candidate_is_exactly_bound() -> None:
    candidate = _load(PROMOTION / "candidate.json")
    assert candidate["repository"] == REPO
    assert HEX40.match(candidate["commit"]), "candidate must be an immutable revision"
    assert candidate["record"] is None, "MNCS carries no self development record by design"
    for obligation in candidate["obligations"]:
        assert (ROOT / obligation).is_file()


def test_boundary_requires_validation_obligations_and_self() -> None:
    boundary = _load(PROMOTION / "mncs-promotion.boundary.json")
    assert boundary["schema_version"] == "mncs-promotion-boundary/0.1"
    assert boundary["boundary_id"] == "mncs-promotion"
    assert boundary["subject_repository"] == REPO
    assert boundary["require_subject_binding"] is True
    required = {entry["check_id"]: entry for entry in boundary["required_evidence"]}
    assert set(required) == {"mncs-validation", "mncds-obligations", "promotion-boundary"}
    assert required["mncs-validation"]["authority"] == "machine-native-complexity-standard"
    assert required["mncs-validation"]["contract_revision"] == "0.2"
    assert (
        required["mncds-obligations"]["authority"]
        == "machine-native-complexity-development-specification"
    )
    assert required["promotion-boundary"]["authority"] == ("machine-native-complexity-standard")
    assert boundary["obligation_check_id"] == "mncds-obligations"
    assert boundary["tolerated_obligations"] == []


def test_authority_map_covers_boundary_requirements() -> None:
    boundary = _load(PROMOTION / "mncs-promotion.boundary.json")
    authority_map = _load(PROMOTION / "authority-map.json")
    assert authority_map["schema_version"] == "mncs-authority-map/0.1"
    for entry in boundary["required_evidence"]:
        binding = authority_map["authorities"][entry["check_id"]]
        assert binding["authority"] == entry["authority"]
    assert authority_map["authorities"]["mncs-validation"]["provider"] == "mncs-validator-rs"
    assert authority_map["authorities"]["mncds-obligations"]["provider"] == "mncds"
    assert (
        authority_map["authorities"]["promotion-boundary"]["provider"] == "mncs-promotion-boundary"
    )


def test_obligations_are_candidate_bound_with_resolved_required() -> None:
    candidate = _load(PROMOTION / "candidate.json")
    records = [_load(ROOT / path) for path in candidate["obligations"]]
    assert records, "candidate must carry at least one obligation record"
    for record in records:
        assert record["schema_version"] == "mncds-obligation-record/0.2"
        assert record["subject"] == {
            "repository": candidate["repository"],
            "commit": candidate["commit"],
        }
        assert record["status"] in ("open", "resolved", "rejected")
    required_open = [r for r in records if r.get("required") and r["status"] == "open"]
    assert not required_open, "no required obligation may be open at the candidate"
    assert any(r.get("required") and r["status"] == "resolved" for r in records)


def test_evaluator_skips_self_without_approving(tmp_path: Path) -> None:
    candidate = _load(PROMOTION / "candidate.json")
    check = {
        "schema_version": "mncs.check-result/1",
        "id": "mncs-validation",
        "provider": "mncs-validator-rs",
        "verdict": "PASS",
        "contract_revision": "0.2",
        "subject": {"repository": REPO, "commit": candidate["commit"]},
    }
    check_path = tmp_path / "mncs-check.json"
    check_path.write_text(json.dumps(check), encoding="utf-8")
    obligations_check = {
        "schema_version": "mncs.check-result/1",
        "id": "mncds-obligations",
        "provider": "mncds",
        "verdict": "PASS",
        "contract_revision": "mncds-obligation-record/0.2",
        "subject": {"repository": REPO, "commit": candidate["commit"]},
    }
    obligations_check_path = tmp_path / "mncds-obligations-check.json"
    obligations_check_path.write_text(json.dumps(obligations_check), encoding="utf-8")
    out = tmp_path / "promotion-check.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/mncs_promotion_evaluate.py"),
            "--boundary",
            str(PROMOTION / "mncs-promotion.boundary.json"),
            "--authority-map",
            str(PROMOTION / "authority-map.json"),
            "--checks",
            str(check_path),
            str(obligations_check_path),
            "--obligations",
            str(PROMOTION / "obligations/promotion-self-reference.obligation.json"),
            str(PROMOTION / "obligations/promotion-adoption.obligation.json"),
            "--subject-repository",
            REPO,
            "--subject-commit",
            candidate["commit"],
            "--check-id",
            "promotion-boundary",
            "--output",
            str(out),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["verdict"] == "PASS"
    assert doc["promotion"]["required_total"] == 2
    assert doc["promotion"]["required_passed"] == 2
    assert any("own output" in note for note in doc.get("unresolved", []))
