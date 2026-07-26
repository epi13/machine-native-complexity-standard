# SPDX-License-Identifier: Apache-2.0

import json
import shutil
from pathlib import Path
from typing import Any

from mncs_validator.hashing import hash_path
from mncs_validator.validation import compute_acceptance, validate_bundle, validate_manifest

ROOT = Path(__file__).resolve().parents[1]


def _manifest() -> dict[str, Any]:
    return json.loads((ROOT / "examples/minimal/manifest.json").read_text())


def test_valid_manifest_and_bundle() -> None:
    manifest = ROOT / "examples/minimal/manifest.json"
    assert validate_manifest(manifest).valid
    report = validate_bundle(manifest.parent)
    assert report.valid
    assert report.computed_status == "PASS"


def test_missing_evidence(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(ROOT / "examples/minimal", bundle)
    (bundle / "evidence/behavioral.json").unlink()
    report = validate_bundle(bundle)
    assert not report.valid
    assert "missing-evidence" in {issue.code for issue in report.issues}


def test_hash_mismatch(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(ROOT / "examples/minimal", bundle)
    (bundle / "machine/generated.py").write_text("# MNCS-GENERATED\nchanged\n")
    report = validate_bundle(bundle)
    assert not report.valid
    assert "hash-mismatch" in {issue.code for issue in report.issues}


def test_unknown_is_never_pass() -> None:
    manifest = _manifest()
    manifest["acceptance_policy"]["behavioral_pass"] = "UNKNOWN"
    assert compute_acceptance(manifest) == "UNKNOWN"
    manifest["acceptance_policy"]["compiler_matrix_pass"] = "FAIL"
    assert compute_acceptance(manifest) == "FAIL"


def test_cumulative_level_gates() -> None:
    manifest = _manifest()
    manifest["claimed_level"] = "MNCS-L2"
    manifest["acceptance_policy"]["safety_pass"] = "PASS"
    manifest["acceptance_policy"]["resource_bounds_pass"] = "UNKNOWN"
    assert compute_acceptance(manifest) == "UNKNOWN"
    manifest["acceptance_policy"]["resource_bounds_pass"] = "PASS"
    assert compute_acceptance(manifest) == "PASS"


def test_path_escape_is_rejected_before_hashing(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(ROOT / "examples/minimal", bundle)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["reference"]["path"] = "../outside.py"
    manifest_path.write_text(json.dumps(manifest))
    (tmp_path / "outside.py").write_text("secret")
    report = validate_manifest(manifest_path)
    assert not report.valid
    assert any(issue.code in {"schema", "unsafe-path"} for issue in report.issues)


def test_directory_cannot_substitute_for_evidence(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    shutil.copytree(ROOT / "examples/minimal", bundle)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["reference"] = {
        "path": "reference",
        "sha256": hash_path(bundle / "reference"),
    }
    manifest_path.write_text(json.dumps(manifest))
    report = validate_manifest(manifest_path)
    assert not report.valid
    assert "invalid-evidence-type" in {issue.code for issue in report.issues}


def test_bundle_layout_is_required(tmp_path: Path) -> None:
    bundle = tmp_path / "empty"
    bundle.mkdir()
    report = validate_bundle(bundle)
    assert not report.valid
    assert "bundle-layout" in {issue.code for issue in report.issues}
