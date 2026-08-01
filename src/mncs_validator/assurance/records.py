"""Threat and measurement profile semantic checks."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime
from typing import Any

from .common import objects, schema_report
from .freshness import freshness_status
from .model import AssuranceValidationReport
from .status import aggregate_status


def validate_threat_value(
    value: dict[str, Any],
    *,
    target: str = "$",
) -> AssuranceValidationReport:
    """Validate a portable threat record without testing its mitigations."""

    report = schema_report(value, "threat", target)
    if not report.valid:
        return report
    computed = aggregate_status(
        [str(item.get("status")) for item in objects(value.get("mitigations"))]
    )
    report.rule_results["MNCS-03-THREAT-STATUS"] = computed
    report.computed_status = computed
    if value.get("status") != computed:
        report.add(
            "MNCS-03-THREAT-RESULT-MISMATCH",
            f"threat declares {value.get('status')!r}, expected {computed}",
            "$/status",
        )
    return report


def validate_measurement_value(
    value: dict[str, Any],
    *,
    target: str = "$",
    at: datetime | None = None,
) -> AssuranceValidationReport:
    """Validate a measurement protocol without executing a benchmark."""

    report = schema_report(value, "measurement", target)
    if not report.valid:
        return report
    statuses = [freshness_status(value.get("freshness"), at)]
    if value.get("reporting_mode") == "best_run_only":
        statuses.append("FAIL")
        report.warn(
            "MNCS-03-MEASUREMENT-BEST-RUN",
            "best-run-only reporting is prohibited",
            "$/reporting_mode",
        )
    computed = aggregate_status(statuses)
    report.rule_results["MNCS-03-MEASUREMENT-PROTOCOL"] = computed
    report.computed_status = computed
    if value.get("status") != computed:
        report.add(
            "MNCS-03-MEASUREMENT-RESULT-MISMATCH",
            f"measurement declares {value.get('status')!r}, expected {computed}",
            "$/status",
        )
    return report
