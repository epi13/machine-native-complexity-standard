"""Partial and full revalidation sufficiency.

The caller supplies assessments and evidence identities. This module verifies
coverage; it does not execute or regenerate any evidence.
"""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from .common import objects, strings
from .graph import material_change_impact
from .status import Status, aggregate_status


def derive_revalidation(
    value: dict[str, Any],
    claim_ids: set[str],
    dependencies: list[dict[str, Any]],
) -> tuple[Status, set[str], set[str]]:
    """Derive status plus direct and transitive material-change impact."""

    changes = objects(value.get("material_changes"))
    material = [change for change in changes if change.get("material") is True]
    direct, affected = material_change_impact(material, dependencies)
    revalidation = value.get("revalidation")
    impact = value.get("evidence_impact")
    if not isinstance(revalidation, dict) or not isinstance(impact, dict):
        return "UNKNOWN", direct, affected
    impact_status = str(impact.get("status", "UNKNOWN"))
    mode = revalidation.get("mode")
    if not material:
        return (
            aggregate_status([impact_status, str(revalidation.get("status", "UNKNOWN"))]),
            direct,
            affected,
        )
    if mode == "none":
        return aggregate_status([impact_status, "UNKNOWN"]), direct, affected
    scope = strings(revalidation.get("scope_claim_ids"))
    covered = strings(revalidation.get("covered_change_ids"))
    material_ids = {
        str(change["change_id"]) for change in material if isinstance(change.get("change_id"), str)
    }
    invalidated = strings(impact.get("invalidated_evidence_ids"))
    retained = strings(revalidation.get("retained_evidence_ids"))
    required_new = strings(impact.get("required_new_evidence_ids"))
    new = strings(revalidation.get("new_evidence_ids"))
    sufficient = (
        affected <= scope
        and material_ids <= covered
        and not invalidated.intersection(retained)
        and required_new <= new
        and affected <= claim_ids
    )
    if mode == "full":
        sufficient = sufficient and claim_ids <= scope
    if impact_status == "FAIL":
        return "FAIL", direct, affected
    return (
        "PASS" if sufficient and impact_status == "PASS" else "UNKNOWN",
        direct,
        affected,
    )
