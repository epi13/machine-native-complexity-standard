# SPDX-License-Identifier: Apache-2.0

import copy
import json
from pathlib import Path

from mncs_validator.schemas import SCHEMA_NAMES, load_schema, schema_errors

ROOT = Path(__file__).resolve().parents[1]


def test_all_packaged_schemas_are_draft_2020_12_and_self_valid() -> None:
    for name in SCHEMA_NAMES:
        schema = load_schema(name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_current_gate_result_requires_positive_pass_evidence() -> None:
    path = ROOT / "examples/minimal/evidence/gate-behavioral.json"
    result = json.loads(path.read_text())
    assert schema_errors(result, "gate-result") == []
    result["evidence_references"] = []
    result["observation_counts"] = {"total": 0, "passed": 0, "failed": 0, "unknown": 0}
    errors = schema_errors(result, "gate-result")
    assert errors
    assert any("non-empty" in error or "greater than" in error for error in errors)


def test_level_conditional_manifest_requirements_are_cumulative() -> None:
    path = ROOT / "examples/minimal/manifest.json"
    manifest = json.loads(path.read_text())
    assert schema_errors(manifest, "manifest") == []
    manifest["claimed_level"] = "MNCS-L3"
    manifest["acceptance_policy"]["conformance_level"] = "MNCS-L3"
    errors = schema_errors(manifest, "manifest")
    assert errors
    assert any("fuzz_evidence" in error or "invariants" in error for error in errors)


def test_legacy_schemas_remain_available() -> None:
    legacy = json.loads((ROOT / "examples/legacy-0.1/manifest.json").read_text())
    assert schema_errors(legacy, "manifest-0.1") == []
    assert schema_errors(legacy, "manifest")


def test_extension_namespace_and_shadowing_schema_boundary() -> None:
    gate = json.loads((ROOT / "examples/minimal/evidence/gate-behavioral.json").read_text())
    gate["extensions"] = {"vendor.example:mode": {"bounded": True}}
    assert schema_errors(gate, "gate-result") == []
    gate["extensions"] = {"mode": True}
    assert schema_errors(gate, "gate-result")


def test_custom_namespaced_gate_is_schema_valid() -> None:
    gate = json.loads((ROOT / "examples/minimal/evidence/gate-behavioral.json").read_text())
    gate["result_id"] = "vendor-quality-result"
    gate["gate_kind"] = "vendor.example:quality"
    assert schema_errors(gate, "gate-result") == []
    manifest = json.loads((ROOT / "examples/minimal/manifest.json").read_text())
    manifest["acceptance_policy"]["required_gates"].append("vendor.example:quality")
    manifest["gate_results"]["vendor.example:quality"] = ["vendor-quality-result"]
    assert schema_errors(manifest, "manifest") == []


def test_nonfinite_numbers_are_rejected() -> None:
    performance = json.loads(
        (ROOT / "examples/http-chunked-decoder/evidence/performance.json").read_text()
    )
    changed = copy.deepcopy(performance)
    changed["candidate_samples"][0] = float("inf")
    assert any("nonfinite" in error for error in schema_errors(changed, "performance-result"))
