# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

from mncs_validator.schemas import schema_errors

ROOT = Path(__file__).resolve().parents[1]


def _load_provider() -> ModuleType:
    path = ROOT / "experimental/mnea/clang_provider.py"
    spec = importlib.util.spec_from_file_location("experimental_mnea_clang", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_foundation_example_records_validate() -> None:
    examples = {
        "contract-profile": ROOT / "examples/foundation/contract-profile.json",
        "assurance-case": ROOT / "examples/foundation/assurance-case.json",
        "analyzer-result": ROOT / "examples/foundation/analyzer-result.json",
    }
    for schema_name, path in examples.items():
        value = json.loads(path.read_text())
        assert schema_errors(value, schema_name) == []


def test_assurance_case_preserves_separate_claim_statuses() -> None:
    path = ROOT / "examples/foundation/assurance-case.json"
    value = json.loads(path.read_text())
    value["mncs"]["status"] = "FAIL"
    value["mncds"]["status"] = "PASS"
    assert schema_errors(value, "assurance-case") == []
    assert "final_status" not in value


def test_analyzer_pass_requires_complete_required_semantics() -> None:
    path = ROOT / "examples/foundation/analyzer-result.json"
    value = json.loads(path.read_text())
    value["required_semantics_complete"] = False
    assert schema_errors(value, "analyzer-result")


def test_forbidden_call_and_unknown_semantics() -> None:
    provider = _load_provider()
    facts = provider.Facts(
        functions={"decode"},
        calls={"decode": {"strcpy"}},
        call_locations={"strcpy": ["candidate.c:10:3"]},
    )
    failed = provider.evaluate_invariant(
        {"id": "no-strcpy", "kind": "forbidden_calls", "calls": ["strcpy"]}, facts
    )
    assert failed.status == "FAIL"
    unresolved = provider.Facts(
        functions={"decode"},
        calls={"decode": set()},
        unresolved_calls=["candidate.c:11:3"],
    )
    unknown = provider.evaluate_invariant(
        {"id": "no-recursion", "kind": "no_recursion"}, unresolved
    )
    assert unknown.status == "UNKNOWN"


def test_analyzer_status_dominance() -> None:
    provider = _load_provider()
    passed = provider.InvariantResult("a", "PASS", "passed")
    unknown = provider.InvariantResult("b", "UNKNOWN", "unknown")
    failed = provider.InvariantResult("c", "FAIL", "failed")
    assert provider.aggregate([passed]) == "PASS"
    assert provider.aggregate([passed, unknown]) == "UNKNOWN"
    assert provider.aggregate([passed, unknown, failed]) == "FAIL"
