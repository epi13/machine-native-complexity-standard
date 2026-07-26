"""Packaged JSON Schema discovery and validation."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import math
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from .errors import SchemaNotFoundError

SCHEMA_NAMES = {
    "manifest": "mncs-manifest.schema.json",
    "gate-result": "mncs-gate-result.schema.json",
    "identity": "mncs-identity.schema.json",
    "invariant-result": "mncs-invariant-result.schema.json",
    "evidence-index": "mncs-evidence-index.schema.json",
    "performance-result": "mncs-performance-result.schema.json",
    "provenance": "mncs-provenance.schema.json",
    "tool-provider": "mncs-tool-provider.schema.json",
    "manifest-0.1": "mncs-manifest-0.1.schema.json",
    "invariant-result-0.1": "mncs-invariant-result-0.1.schema.json",
    "evidence-index-0.1": "mncs-evidence-index-0.1.schema.json",
    "performance-result-0.1": "mncs-performance-result-0.1.schema.json",
    "provenance-0.1": "mncs-provenance-0.1.schema.json",
    "tool-provider-0.1": "mncs-tool-provider-0.1.schema.json",
}


def schema_path(name: str) -> Traversable:
    """Resolve a schema strictly from installed package resources."""

    filename = SCHEMA_NAMES.get(name, name)
    if filename not in SCHEMA_NAMES.values():
        raise SchemaNotFoundError(f"unknown schema: {name}")
    candidate = files("mncs_validator.resources.schemas").joinpath(filename)
    if not candidate.is_file():
        raise SchemaNotFoundError(f"schema is not installed: {filename}")
    return candidate


def load_schema(name: str) -> dict[str, Any]:
    """Load and self-check a packaged schema."""

    value: Any = json.loads(schema_path(name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SchemaError(f"schema {name} is not an object")
    Draft202012Validator.check_schema(value)
    return value


def _nonfinite_paths(value: Any, path: str = "$") -> list[str]:
    if isinstance(value, float) and not math.isfinite(value):
        return [f"{path}: nonfinite numbers are forbidden"]
    if isinstance(value, dict):
        return [
            finding
            for key, child in value.items()
            for finding in _nonfinite_paths(child, f"{path}/{key}")
        ]
    if isinstance(value, list):
        return [
            finding
            for index, child in enumerate(value)
            for finding in _nonfinite_paths(child, f"{path}/{index}")
        ]
    return []


def schema_errors(instance: Any, name: str) -> list[str]:
    """Return stable human-readable schema and numeric validation errors."""

    validator = Draft202012Validator(load_schema(name), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    rendered = _nonfinite_paths(instance)
    for error in errors:
        location = "/".join(str(part) for part in error.absolute_path) or "$"
        rendered.append(f"{location}: {error.message}")
    return sorted(rendered)
