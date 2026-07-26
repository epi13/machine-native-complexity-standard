# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

from mncs_validator.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_version_reports_all_version_concepts(capsys: object) -> None:
    assert main(["version", "--json"]) == 0
    value = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert value == {
        "current_schema_version": "0.2",
        "normative_standard_family": "MNCS 0.2",
        "package": "mncs-validator",
        "package_version": "0.2.0",
        "supported_schema_versions": ["0.1", "0.1.1", "0.2"],
    }


def test_validate_and_certify_exit_contract(capsys: object) -> None:
    passed = ROOT / "examples/minimal/manifest.json"
    failed = ROOT / "examples/rejected-candidate/manifest.json"
    invalid = ROOT / "conformance-corpus/invalid/final-status-mismatch/manifest.json"
    assert main(["validate", str(passed)]) == 0
    assert main(["validate", str(failed)]) == 0
    assert main(["certify", str(passed)]) == 0
    assert main(["certify", str(failed)]) == 3
    assert main(["validate", str(failed), "--require-pass"]) == 3
    assert main(["validate", str(invalid)]) == 1
    assert main(["validate", str(ROOT / "absent.json")]) == 2
    capsys.readouterr()  # type: ignore[attr-defined]


def test_legacy_certification_requires_explicit_override(capsys: object) -> None:
    legacy = ROOT / "examples/legacy-0.1/manifest.json"
    assert main(["validate", str(legacy)]) == 0
    assert main(["certify", str(legacy)]) == 3
    capsys.readouterr()  # type: ignore[attr-defined]
    assert main(["certify", str(legacy), "--allow-legacy", "--json"]) == 0
    value = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert value["legacy_override_used"] is True
    assert value["reduced_assurance"] is True


def test_schema_lookup_json(capsys: object) -> None:
    assert main(["schema", "manifest", "--json"]) == 0
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert json.loads(captured.out)["title"] == "MNCS evidence-derived conformance manifest"


def test_hash_summarize_and_init(capsys: object, tmp_path: Path) -> None:
    assert main(["hash", str(ROOT / "NOTICE"), "--json"]) == 0
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert json.loads(captured.out)["sha256"].startswith("sha256:")
    assert main(["summarize", str(ROOT / "examples/minimal/manifest.json")]) == 0
    target = tmp_path / "bundle"
    assert main(["init", str(target), "--json"]) == 0
    template = json.loads((target / "manifest.template.json").read_text())
    assert template["schema_version"] == "0.2"


def test_init_refuses_nonempty_directory(tmp_path: Path) -> None:
    target = tmp_path / "bundle"
    target.mkdir()
    (target / "existing").write_text("preserve")
    assert main(["init", str(target)]) == 2
    assert (target / "existing").read_text() == "preserve"
