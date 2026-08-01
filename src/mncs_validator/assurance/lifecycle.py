"""Supersession, replacement, rollback, and retirement checks."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from .model import AssuranceValidationReport
from .status import Status, aggregate_status


def apply_lifecycle(
    value: dict[str, Any],
    claims: dict[str, dict[str, Any]],
    root_claim_id: object,
    root: dict[str, Any],
    root_status: Status,
    report: AssuranceValidationReport,
) -> Status:
    """Validate lifecycle bindings and return their dominant root status."""

    lifecycle = value.get("lifecycle")
    if not isinstance(lifecycle, dict):
        return aggregate_status([root_status, "UNKNOWN"])
    supersession = lifecycle.get("supersession")
    if isinstance(supersession, dict) and supersession.get("prior_assurance_case_id") == value.get(
        "assurance_case_id"
    ):
        report.add(
            "MNCS-03-SELF-SUPERSESSION",
            "an assurance case cannot supersede itself",
            "$/lifecycle/supersession",
        )
    replacement = lifecycle.get("replacement")
    if isinstance(replacement, dict):
        if replacement.get("old_artifact_id") == replacement.get("new_artifact_id"):
            report.add(
                "MNCS-03-REPLACEMENT-IDENTITY",
                "replacement requires a new artifact identity",
                "$/lifecycle/replacement",
            )
        if replacement.get("old_claim_id") == replacement.get("new_claim_id"):
            report.add(
                "MNCS-03-REPLACEMENT-CLAIM-IDENTITY",
                "replacement requires a new claim identity",
                "$/lifecycle/replacement",
            )
        for field_name in ("old_claim_id", "new_claim_id"):
            if replacement.get(field_name) not in claims:
                report.add(
                    "MNCS-03-REPLACEMENT-CLAIM-MISSING",
                    f"replacement {field_name} does not resolve",
                    f"$/lifecycle/replacement/{field_name}",
                )
        root_status = aggregate_status([root_status, str(replacement.get("status", "UNKNOWN"))])
    rollback = lifecycle.get("rollback")
    if isinstance(rollback, dict):
        rollback_status = str(rollback.get("test_status", "UNKNOWN"))
        if rollback.get("active_release_id") != value.get("release_id"):
            rollback_status = "FAIL"
            report.warn(
                "MNCS-03-ROLLBACK-BINDING",
                "rollback is bound to a different release",
                "$/lifecycle/rollback/active_release_id",
            )
        if rollback.get("environment_id") != root.get("environment_id"):
            rollback_status = "FAIL"
            report.warn(
                "MNCS-03-ROLLBACK-ENVIRONMENT",
                "rollback is bound to a different environment",
                "$/lifecycle/rollback/environment_id",
            )
        root_status = aggregate_status([root_status, rollback_status])
    retirement = lifecycle.get("retirement")
    if isinstance(retirement, dict):
        retired_id = retirement.get("claim_id")
        retired_claim = claims.get(str(retired_id))
        if retired_claim is None:
            report.add(
                "MNCS-03-RETIREMENT-CLAIM-MISSING",
                "retirement references an unknown claim",
                "$/lifecycle/retirement/claim_id",
            )
        elif retired_claim.get("retired") is not True:
            report.add(
                "MNCS-03-RETIREMENT-INCONSISTENT",
                "retirement claim is not marked retired",
                "$/lifecycle/retirement/claim_id",
            )
        if retired_id == root_claim_id:
            root_status = "FAIL"
    return root_status
