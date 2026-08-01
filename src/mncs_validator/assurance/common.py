"""Bounded record helpers shared by semantic modules."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, cast

from ..schemas import schema_errors
from .model import AssuranceValidationReport, RecordKind

SCHEMAS: dict[RecordKind, str] = {
    "contract": "contract-profile-0.3",
    "assurance": "assurance-case-0.3",
    "threat": "threat-record-0.3",
    "measurement": "measurement-profile-0.3",
}


def objects(value: object) -> list[dict[str, Any]]:
    """Return object members of a list; schema validation handles other members."""

    if not isinstance(value, list):
        return []
    return [cast(dict[str, Any], item) for item in value if isinstance(item, dict)]


def strings(value: object) -> set[str]:
    """Return string members as an order-independent set."""

    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def schema_report(
    value: dict[str, Any],
    kind: RecordKind,
    target: str,
) -> AssuranceValidationReport:
    """Create a report and apply the packaged non-executable JSON Schema."""

    report = AssuranceValidationReport(target=target, kind=kind)
    identity_keys = {
        "contract": "profile_id",
        "assurance": "assurance_case_id",
        "threat": "threat_id",
        "measurement": "profile_id",
    }
    identity = value.get(identity_keys[kind])
    report.record_id = identity if isinstance(identity, str) else None
    for error in schema_errors(value, SCHEMAS[kind]):
        report.add("SCHEMA", error)
    return report


def unique_map(
    values: list[dict[str, Any]],
    key: str,
    report: AssuranceValidationReport,
    path: str,
    code: str,
) -> dict[str, dict[str, Any]]:
    """Index unique identities while preserving duplicate findings."""

    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(values):
        identity = item.get(key)
        if not isinstance(identity, str):
            continue
        if identity in result:
            report.add(code, f"duplicate identity: {identity}", f"{path}/{index}/{key}")
        result[identity] = item
    return result
