"""Offline contract-adequacy semantic checks."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from .common import objects, schema_report
from .model import AssuranceValidationReport
from .status import aggregate_status


def validate_contract_value(
    value: dict[str, Any],
    *,
    target: str = "$",
) -> AssuranceValidationReport:
    """Validate declared contract adequacy without evaluating a candidate."""

    report = schema_report(value, "contract", target)
    if not report.valid:
        return report
    statuses = [
        str(finding.get("status"))
        for finding in objects(value.get("findings"))
        if finding.get("required") is True
    ]
    if value.get("correctness_basis") == "candidate_behavior":
        statuses.append("FAIL")
        report.warn(
            "MNCS-03-CONTRACT-CIRCULAR",
            "correctness cannot be defined by candidate behavior",
            "$/correctness_basis",
        )
    behavior = value.get("behavior")
    if isinstance(behavior, dict) and not behavior.get("malformed_inputs"):
        statuses.append("FAIL")
        report.warn(
            "MNCS-03-CONTRACT-MALFORMED-MISSING",
            "malformed-input behavior is required",
            "$/behavior/malformed_inputs",
        )
    limits = value.get("limits")
    if isinstance(limits, dict):
        for name in ("resource", "timing"):
            applicability = limits.get(f"{name}_applicability")
            applicable = isinstance(applicability, dict) and applicability.get("applicable") is True
            if applicable and not limits.get(name):
                statuses.append("FAIL")
                report.warn(
                    f"MNCS-03-CONTRACT-{name.upper()}-MISSING",
                    f"applicable {name} limits are missing",
                    f"$/limits/{name}",
                )
    for ambiguity in objects(value.get("ambiguities")):
        if ambiguity.get("material") is True:
            statuses.append(
                "FAIL" if ambiguity.get("demonstrated_violation") is True else "UNKNOWN"
            )
    computed = aggregate_status(statuses)
    report.rule_results["MNCS-03-CONTRACT-ADEQUACY"] = computed
    report.computed_status = computed
    if value.get("status") != computed:
        report.add(
            "MNCS-03-CONTRACT-RESULT-MISMATCH",
            f"declared contract status {value.get('status')!r} does not equal {computed}",
            "$/status",
        )
    return report
