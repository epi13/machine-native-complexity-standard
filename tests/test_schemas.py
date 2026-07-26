# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

from mncs_validator.schemas import SCHEMA_NAMES, load_schema, schema_errors

ROOT = Path(__file__).resolve().parents[1]


def test_all_schemas_are_draft_2020_12_and_self_valid() -> None:
    for name in SCHEMA_NAMES:
        schema = load_schema(name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_valid_tool_provider_fixture() -> None:
    value = json.loads((ROOT / "tests/fixtures/valid-tool-provider.json").read_text())
    assert schema_errors(value, "tool-provider") == []


def test_intentionally_invalid_manifest_fixture() -> None:
    value = json.loads((ROOT / "tests/fixtures/invalid-manifest.json").read_text())
    errors = schema_errors(value, "manifest")
    assert errors
    assert any("MNCS-L99" in error for error in errors)


def test_extension_namespace_is_accepted_and_unqualified_key_is_rejected() -> None:
    provider = json.loads((ROOT / "tests/fixtures/valid-tool-provider.json").read_text())
    provider["extensions"] = {"vendor.example:mode": {"bounded": True}}
    assert schema_errors(provider, "tool-provider") == []
    provider["extensions"] = {"mode": True}
    assert schema_errors(provider, "tool-provider")
