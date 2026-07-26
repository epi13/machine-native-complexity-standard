"""Schema discovery and JSON Schema validation."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from .errors import SchemaNotFoundError

SCHEMA_NAMES = {
    "manifest": "mncs-manifest.schema.json",
    "invariant-result": "mncs-invariant-result.schema.json",
    "evidence-index": "mncs-evidence-index.schema.json",
    "performance-result": "mncs-performance-result.schema.json",
    "provenance": "mncs-provenance.schema.json",
    "tool-provider": "mncs-tool-provider.schema.json",
}


def schema_directories() -> list[Path]:
    """Return ordered development and installed schema locations."""

    package_root = Path(__file__).resolve().parents[2]
    return [
        package_root / "schemas",
        Path.cwd() / "schemas",
        Path(sys.prefix) / "share" / "mncs" / "schemas",
    ]


def schema_path(name: str) -> Path:
    """Resolve a public schema name without network access."""

    filename = SCHEMA_NAMES.get(name, name)
    if filename not in SCHEMA_NAMES.values():
        raise SchemaNotFoundError(f"unknown schema: {name}")
    for directory in schema_directories():
        candidate = directory / filename
        if candidate.is_file():
            return candidate
    raise SchemaNotFoundError(f"schema is not installed: {filename}")


def load_schema(name: str) -> dict[str, Any]:
    """Load and self-check a schema."""

    value: Any = json.loads(schema_path(name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SchemaError(f"schema {name} is not an object")
    Draft202012Validator.check_schema(value)
    return value


def schema_errors(instance: Any, name: str) -> list[str]:
    """Return stable human-readable validation errors."""

    validator = Draft202012Validator(load_schema(name), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    rendered: list[str] = []
    for error in errors:
        location = "/".join(str(part) for part in error.absolute_path) or "$"
        rendered.append(f"{location}: {error.message}")
    return rendered
