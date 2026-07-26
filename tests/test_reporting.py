# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

from mncs_validator.reporting import manifest_summary, render_summary, render_validation
from mncs_validator.validation import validate_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_summary_contains_claim_and_unknown_count() -> None:
    path = ROOT / "examples/minimal/manifest.json"
    summary = manifest_summary(json.loads(path.read_text()))
    text = render_summary(summary)
    assert "MNCS-L1 (PASS)" in text
    assert "unresolved UNKNOWN" in text


def test_validation_render_is_deterministic() -> None:
    path = ROOT / "examples/minimal/manifest.json"
    report = validate_manifest(path)
    assert render_validation(report).startswith("VALID:")
