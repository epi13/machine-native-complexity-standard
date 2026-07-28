"""Packaged JSON Schema discovery and validation."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import math
from copy import deepcopy
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Any, cast

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
    "canonical-document": "mncs-canonical-document.schema.json",
    "attestation-envelope": "mncs-attestation-envelope.schema.json",
    "attestation-statement": "mncs-attestation-statement.schema.json",
    "subject-identity": "mncs-subject-identity.schema.json",
    "trust-policy": "mncs-trust-policy.schema.json",
    "key-record": "mncs-key-record.schema.json",
    "revocation-record": "mncs-revocation-record.schema.json",
    "package-index": "mncs-package-index.schema.json",
    "provider-request": "mncs-provider-request.schema.json",
    "provider-response": "mncs-provider-response.schema.json",
    "provider-capabilities": "mncs-provider-capabilities.schema.json",
    "provider-descriptor": "mncs-provider-descriptor.schema.json",
    "provider-error": "mncs-provider-error.schema.json",
    "mncds-development-record": "mncds-development-record.schema.json",
    "contract-profile": "mncs-contract-profile.schema.json",
    "assurance-case": "mncs-assurance-case.schema.json",
    "analyzer-result": "mncs-analyzer-result.schema.json",
    "language-evidence-profile": "mncs-language-evidence-profile.schema.json",
    "cross-language-comparison": "mncs-cross-language-comparison.schema.json",
    "boundary-contract": "mncs-boundary-contract.schema.json",
    "composed-assurance-case": "mncs-composed-assurance-case.schema.json",
    "composed-evidence-epoch": "mncs-composed-evidence-epoch.schema.json",
    "evidence-custody": "mncs-evidence-custody.schema.json",
    "cross-host-agreement": "mncs-cross-host-agreement.schema.json",
    "claim-readiness": "mncs-claim-readiness.schema.json",
    "manifest-0.1.1": "mncs-manifest.schema.json",
    "gate-result-0.1.1": "mncs-gate-result.schema.json",
    "identity-0.1.1": "mncs-identity.schema.json",
    "invariant-result-0.1.1": "mncs-invariant-result.schema.json",
    "evidence-index-0.1.1": "mncs-evidence-index.schema.json",
    "performance-result-0.1.1": "mncs-performance-result.schema.json",
    "provenance-0.1.1": "mncs-provenance.schema.json",
    "tool-provider-0.1.1": "mncs-tool-provider.schema.json",
    "manifest-0.1": "mncs-manifest-0.1.schema.json",
    "invariant-result-0.1": "mncs-invariant-result-0.1.schema.json",
    "evidence-index-0.1": "mncs-evidence-index-0.1.schema.json",
    "performance-result-0.1": "mncs-performance-result-0.1.schema.json",
    "provenance-0.1": "mncs-provenance-0.1.schema.json",
    "tool-provider-0.1": "mncs-tool-provider-0.1.schema.json",
}


def schema_path(name: str) -> Traversable:
    filename = SCHEMA_NAMES.get(name, name)
    if filename not in SCHEMA_NAMES.values():
        raise SchemaNotFoundError(f"unknown schema: {name}")
    candidate = files("mncs_validator.resources.schemas").joinpath(filename)
    if not candidate.is_file():
        raise SchemaNotFoundError(f"schema is not installed: {filename}")
    return candidate


def load_schema(name: str) -> dict[str, Any]:
    value: Any = json.loads(schema_path(name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SchemaError(f"schema {name} is not an object")
    if name.endswith("-0.1.1"):
        value = _legacy_0_1_1_schema(value)
    Draft202012Validator.check_schema(value)
    return cast(dict[str, Any], value)


def _legacy_0_1_1_schema(schema: dict[str, Any]) -> dict[str, Any]:
    value = deepcopy(schema)
    identifier = value.get("$id")
    if isinstance(identifier, str):
        value["$id"] = identifier.replace("/0.2/", "/0.1.1/")
    properties = value.get("properties")
    if isinstance(properties, dict):
        properties["schema_version"] = {"const": "0.1.1"}
        properties["mncs_version"] = {"const": "0.1"}
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
    validator = Draft202012Validator(load_schema(name), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    rendered = _nonfinite_paths(instance)
    for error in errors:
        location = "/".join(str(part) for part in error.absolute_path) or "$"
        rendered.append(f"{location}: {error.message}")
    return sorted(rendered)
