"""Human-readable report rendering."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from .models import ComparisonResult, ValidationReport


def render_validation(report: ValidationReport) -> str:
    """Render a concise deterministic validation report."""

    headline = "VALID" if report.valid else "INVALID"
    lines = [f"{headline}: {report.target}", f"checked files: {report.checked_files}"]
    if report.declared_status is not None:
        lines.append(f"declared status: {report.declared_status}")
    if report.computed_status is not None:
        lines.append(f"computed status: {report.computed_status}")
    lines.append(f"certification eligible: {str(report.certification_eligible).lower()}")
    if report.legacy_self_asserted_acceptance:
        lines.append("legacy self-asserted acceptance: true")
    for gate, decision in sorted(report.gate_statuses.items()):
        lines.append(
            f"gate {gate}: {decision.status} "
            f"(evidence: {', '.join(decision.evidence_ids) or 'none'})"
        )
    lines.extend(
        f"- {issue.code}{f' [{issue.path}]' if issue.path else ''}: {issue.message}"
        for issue in report.issues
    )
    lines.extend(
        f"- warning {warning.code}{f' [{warning.path}]' if warning.path else ''}: {warning.message}"
        for warning in report.warnings
    )
    return "\n".join(lines)


def manifest_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    """Select the stable public summary fields."""

    component = manifest["component"]
    new_schema = manifest.get("schema_version") in {"0.1.1", "0.2"}
    objective = manifest["acceptance_policy"]["objective"] if new_schema else manifest["objective"]
    return {
        "component": component["name"],
        "version": component["version"],
        "contract_id": component["contract_id"],
        "claimed_level": manifest["claimed_level"],
        "final_status": manifest["final_status"],
        "objective": objective,
        "acceptance_model": "evidence-derived" if new_schema else "legacy self-asserted",
        "unresolved_unknown_results": (
            "computed during validation"
            if new_schema
            else manifest["complexity_profile"]["unresolved_unknown_results"]
        ),
        "limitations": manifest["limitations"],
    }


def render_summary(summary: dict[str, Any]) -> str:
    """Render a manifest summary."""

    objective = summary["objective"]
    return "\n".join(
        [
            f"{summary['component']} {summary['version']}",
            f"contract: {summary['contract_id']}",
            f"claim: {summary['claimed_level']} ({summary['final_status']})",
            f"acceptance: {summary['acceptance_model']}",
            (
                f"objective: {objective['metric']} {objective['direction']} "
                f"threshold={objective['threshold']}"
            ),
            f"unresolved UNKNOWN: {summary['unresolved_unknown_results']}",
            "limitations: " + "; ".join(summary["limitations"]),
        ]
    )


def render_comparison(result: ComparisonResult) -> str:
    """Render a Pareto comparison."""

    lines = [result.relation, result.explanation]
    if result.warning:
        lines.append(result.warning)
    lines.extend(
        f"- evidence strength {candidate}: {strength}"
        for candidate, strength in result.evidence_strength.items()
    )
    lines.extend(f"- {name}: {relation}" for name, relation in result.dimensions.items())
    return "\n".join(lines)
