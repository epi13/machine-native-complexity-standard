"""Exact kind/version dispatch for offline RC records."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from ..errors import ManifestError
from ..validation import load_json_object
from .assurance_case import validate_assurance_value
from .contract import validate_contract_value
from .model import AssuranceValidationReport, RecordKind
from .records import validate_measurement_value, validate_threat_value


def validate_rc_value(
    value: dict[str, Any],
    kind: RecordKind,
    *,
    target: str = "$",
    at: datetime | None = None,
) -> AssuranceValidationReport:
    """Dispatch one statically typed supported MNCS 0.3 record kind."""

    if kind == "contract":
        return validate_contract_value(value, target=target)
    if kind == "assurance":
        return validate_assurance_value(value, target=target, at=at)
    if kind == "threat":
        return validate_threat_value(value, target=target)
    return validate_measurement_value(value, target=target, at=at)


def validate_rc_file(
    path: Path,
    kind: RecordKind,
    *,
    at: datetime | None = None,
) -> AssuranceValidationReport:
    """Load one bounded JSON record and validate it without executing evidence."""

    try:
        value = load_json_object(path)
    except ManifestError as exc:
        report = AssuranceValidationReport(target=str(path), kind=kind)
        report.add("INVALID-JSON", str(exc), str(path))
        return report
    version = value.get("schema_version")
    if version != "0.3-rc.1":
        report = AssuranceValidationReport(
            target=str(path), kind=kind, valid=False, supported=False
        )
        report.add(
            "UNSUPPORTED-VERSION",
            f"unsupported {kind} schema version: {version!r}",
            "$/schema_version",
        )
        return report
    return validate_rc_value(value, kind, target=str(path), at=at)
