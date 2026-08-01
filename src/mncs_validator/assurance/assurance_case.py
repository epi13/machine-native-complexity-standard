"""Combined assurance graph and result reconciliation.

This module coordinates narrow graph, revalidation, lifecycle, freshness, and
presentation helpers. MNCS and MNCDS result objects remain separate.
"""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from .common import objects, schema_report, strings, unique_map
from .freshness import freshness_status
from .graph import claim_cycles, derive_claim_statuses
from .lifecycle import apply_lifecycle
from .model import AssuranceValidationReport
from .revalidation import derive_revalidation
from .status import aggregate_status


def _validate_references(
    claims: dict[str, dict[str, Any]],
    dependencies: list[dict[str, Any]],
    groups: dict[str, dict[str, Any]],
    report: AssuranceValidationReport,
) -> None:
    for index, dependency in enumerate(dependencies):
        for field_name in ("source_claim_id", "target_claim_id"):
            identity = dependency.get(field_name)
            if identity not in claims:
                report.add(
                    "MNCS-03-REFERENCE-MISSING",
                    f"dependency references unknown claim: {identity}",
                    f"$/dependencies/{index}/{field_name}",
                )
        for group_id in strings(dependency.get("correlated_failure_group_ids")):
            if group_id not in groups:
                report.add(
                    "MNCS-03-CORRELATION-MISSING",
                    f"dependency references unknown correlated group: {group_id}",
                    f"$/dependencies/{index}/correlated_failure_group_ids",
                )
        if dependency.get("required") is not True:
            target_claim = claims.get(str(dependency.get("target_claim_id")))
            uncertain = (
                target_claim is None
                or target_claim.get("status") != "PASS"
                or dependency.get("interface_compatibility") != "PASS"
                or dependency.get("environment_compatibility") != "PASS"
            )
            source_claim = claims.get(str(dependency.get("source_claim_id")))
            if uncertain and source_claim is not None and not source_claim.get("limitations"):
                report.add(
                    "MNCS-03-OPTIONAL-DEPENDENCY-UNDISCLOSED",
                    "optional uncertainty must remain visible as a limitation",
                    f"$/dependencies/{index}",
                )
    claim_ids = set(claims)
    for index, group in enumerate(groups.values()):
        if not strings(group.get("claim_ids")) <= claim_ids:
            report.add(
                "MNCS-03-CORRELATION-MEMBER-MISSING",
                "correlated group references an unknown claim",
                f"$/correlated_failure_groups/{index}/claim_ids",
            )


def validate_assurance_value(
    value: dict[str, Any],
    *,
    target: str = "$",
    at: datetime | None = None,
) -> AssuranceValidationReport:
    """Validate an MNCS 0.3 assurance graph and lifecycle semantics offline."""

    report = schema_report(value, "assurance", target)
    if not report.valid:
        return report
    claim_list = objects(value.get("claims"))
    claims = unique_map(claim_list, "claim_id", report, "$/claims", "MNCS-03-DUPLICATE-CLAIM")
    dependencies = objects(value.get("dependencies"))
    unique_map(
        dependencies,
        "dependency_id",
        report,
        "$/dependencies",
        "MNCS-03-DUPLICATE-DEPENDENCY",
    )
    groups = unique_map(
        objects(value.get("correlated_failure_groups")),
        "group_id",
        report,
        "$/correlated_failure_groups",
        "MNCS-03-DUPLICATE-CORRELATION",
    )
    claim_ids = set(claims)
    _validate_references(claims, dependencies, groups, report)
    claim_cycles(claim_ids, dependencies, report)
    if not report.valid:
        return report
    derived = derive_claim_statuses(claims, dependencies, groups, at)
    for index, claim in enumerate(claim_list):
        claim_id = claim.get("claim_id")
        if isinstance(claim_id, str) and claim.get("status") != derived[claim_id]:
            report.add(
                "MNCS-03-CLAIM-RESULT-MISMATCH",
                f"claim {claim_id} declares {claim.get('status')!r}, expected {derived[claim_id]}",
                f"$/claims/{index}/status",
            )
    root_claim_id = value.get("root_claim_id")
    root = claims.get(str(root_claim_id))
    if root is None:
        report.add(
            "MNCS-03-ROOT-CLAIM-MISSING", "root_claim_id does not resolve", "$/root_claim_id"
        )
        return report
    root_status = aggregate_status(
        [
            derived[str(root_claim_id)],
            str(value.get("contract_profile_status", "UNKNOWN")),
            freshness_status(value.get("freshness"), at),
        ]
    )
    revalidation_status, direct, affected = derive_revalidation(value, claim_ids, dependencies)
    report.rule_results["MNCS-03-REVALIDATION"] = revalidation_status
    revalidation = cast(dict[str, Any], value["revalidation"])
    if revalidation.get("status") != revalidation_status:
        report.add(
            "MNCS-03-REVALIDATION-RESULT-MISMATCH",
            f"revalidation declares {revalidation.get('status')!r}, expected {revalidation_status}",
            "$/revalidation/status",
        )
    if affected:
        root_status = aggregate_status([root_status, revalidation_status])
    impact = cast(dict[str, Any], value["evidence_impact"])
    declared_impact = strings(impact.get("affected_claim_ids"))
    if not affected <= declared_impact:
        report.add(
            "MNCS-03-IMPACT-SCOPE-INCOMPLETE",
            "evidence impact omits required transitive graph-affected claims",
            "$/evidence_impact/affected_claim_ids",
        )
    if not direct <= claim_ids:
        report.add(
            "MNCS-03-CHANGE-CLAIM-MISSING",
            "material change references an unknown claim",
            "$/material_changes",
        )
    for index, change in enumerate(objects(value.get("material_changes"))):
        if change.get("material") is True and change.get("old_identity") == change.get(
            "new_identity"
        ):
            report.add(
                "MNCS-03-MATERIAL-IDENTITY-UNCHANGED",
                "a material change requires a new identity",
                f"$/material_changes/{index}",
            )
    root_status = apply_lifecycle(value, claims, root_claim_id, root, root_status, report)
    migration = cast(dict[str, Any], value["migration"])
    if migration.get("downgrade_detected") is True:
        report.add(
            "MNCS-03-DOWNGRADE",
            "a required 0.3 record cannot be replaced by a weaker version",
            "$/migration/downgrade_detected",
        )
    if migration.get("mode") == "wrapped" and migration.get("historical_facts_status") == "PASS":
        report.add(
            "MNCS-03-MIGRATION-PROMOTION",
            "wrapping historical evidence cannot manufacture complete historical facts",
            "$/migration/historical_facts_status",
        )
    mncs = cast(dict[str, Any], value["mncs"])
    for field_name, expected in (
        ("status", root_status),
        ("level", root.get("level")),
        ("result_id", root.get("result_id")),
        ("scope_id", root.get("scope_id")),
    ):
        if mncs.get(field_name) != expected:
            report.add(
                "MNCS-03-ASSURANCE-RESULT-MISMATCH",
                f"mncs.{field_name} does not match the root claim",
                f"$/mncs/{field_name}",
            )
    label = value.get("display_label")
    mncds = value.get("mncds")
    if mncds != root.get("mncds"):
        report.add(
            "MNCS-03-MNCDS-ROOT-MISMATCH",
            "top-level MNCDS result must preserve the root claim development result",
            "$/mncds",
        )
    if label is not None:
        expected_label = (
            f"{mncds.get('profile')} / {mncs.get('level')}" if isinstance(mncds, dict) else None
        )
        if label != expected_label:
            report.add(
                "MNCS-03-DISPLAY-LABEL-MISMATCH",
                "display label does not preserve separate result objects",
                "$/display_label",
            )
    report.rule_results["MNCS-03-ASSURANCE"] = root_status
    report.computed_status = root_status
    return report
