"""Experimental Wave Five portable evaluation and cohort semantics."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

STATUSES = {"PASS", "FAIL", "UNKNOWN"}


def aggregate_status(statuses: Iterable[str]) -> str:
    values = list(statuses)
    if not values or any(value not in STATUSES for value in values):
        return "UNKNOWN"
    if "FAIL" in values:
        return "FAIL"
    if "UNKNOWN" in values:
        return "UNKNOWN"
    return "PASS"


def classify_reproduction_cohort(
    records: list[dict[str, Any]], plan: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Classify a portable evaluator cohort without inferring independence."""

    findings: list[str] = []
    if not records:
        return {
            "status": "UNKNOWN",
            "evidence_class": "NO_EVIDENCE",
            "public_reproduction_status": "UNKNOWN",
            "independent_evaluation_status": "UNKNOWN",
            "findings": ["no host records supplied"],
            "summary": {
                "machine_count": 0,
                "operator_count": 0,
                "os_families": [],
                "distributions": [],
                "architectures": [],
                "semantic_output_digests": [],
            },
        }

    bundle_ids = {record.get("bundle_id") for record in records}
    manifest_ids = {record.get("manifest_identity") for record in records}
    candidate_ids = {record.get("candidate_freeze_identity") for record in records}
    machine_labels = {str(record.get("machine_label", "")) for record in records}
    operator_ids = {str(record.get("operator_id", "")) for record in records}
    environments = [record.get("environment", {}) for record in records]
    os_families = {
        str(environment.get("os_family", "unknown"))
        for environment in environments
        if isinstance(environment, dict)
    }
    distributions = {
        str(environment.get("distribution", "unknown"))
        for environment in environments
        if isinstance(environment, dict)
    }
    architectures = {
        str(environment.get("architecture", "unknown"))
        for environment in environments
        if isinstance(environment, dict)
    }
    digests = {
        str(record.get("semantic_output_digest"))
        for record in records
        if isinstance(record.get("semantic_output_digest"), str)
    }
    result_status = aggregate_status(str(record.get("result", "UNKNOWN")) for record in records)
    gate_status = aggregate_status(
        str(status)
        for record in records
        for status in record.get("gates", {}).values()
        if isinstance(record.get("gates", {}), dict)
    )

    if len(bundle_ids) != 1:
        findings.append("bundle identity mismatch")
    if len(manifest_ids) != 1:
        findings.append("manifest identity mismatch")
    if len(candidate_ids) != 1:
        findings.append("candidate freeze identity mismatch")
    if len(machine_labels) != len(records):
        findings.append("machine labels are missing or duplicated")
    if len(digests) != 1:
        findings.append("semantic output digest mismatch or absence")
    if result_status == "FAIL" or gate_status == "FAIL":
        findings.append("one or more host records failed")
    elif result_status == "UNKNOWN" or gate_status == "UNKNOWN":
        findings.append("one or more host records are unknown")

    required_labels: set[str] = set()
    minimum_hosts = 2
    minimum_os_families = 2
    minimum_distributions = 2
    minimum_architectures = 2
    if plan:
        required_labels = {str(value) for value in plan.get("required_machine_labels", [])}
        thresholds = plan.get("thresholds", {})
        if isinstance(thresholds, dict):
            minimum_hosts = int(thresholds.get("minimum_hosts", minimum_hosts))
            minimum_os_families = int(
                thresholds.get("minimum_os_families", minimum_os_families)
            )
            minimum_distributions = int(
                thresholds.get("minimum_distributions", minimum_distributions)
            )
            minimum_architectures = int(
                thresholds.get("minimum_architectures", minimum_architectures)
            )
    missing_labels = sorted(required_labels - machine_labels)
    if missing_labels:
        findings.append("planned host records are missing: " + ", ".join(missing_labels))

    diversity_satisfied = (
        len(records) >= minimum_hosts
        and len(os_families) >= minimum_os_families
        and len(distributions) >= minimum_distributions
        and len(architectures) >= minimum_architectures
        and not missing_labels
    )
    if not diversity_satisfied:
        findings.append("preregistered host-diversity threshold is not satisfied")

    hard_failure = any("mismatch" in finding or "failed" in finding for finding in findings)
    if hard_failure:
        status = "FAIL"
    elif findings:
        status = "UNKNOWN"
    else:
        status = "PASS"

    if len(records) == 1:
        evidence_class = "SINGLE_HOST"
    elif len(operator_ids) == 1:
        evidence_class = "OPERATOR_CONTROLLED_CROSS_HOST"
    else:
        evidence_class = "MULTI_OPERATOR_PUBLIC_REPRODUCTION"

    public_reproduction_status = "PASS" if status == "PASS" else status
    independent_evaluation_status = "UNKNOWN"
    findings.append(
        "cohort agreement does not establish protected holdout or organizational independence"
    )

    return {
        "status": status,
        "evidence_class": evidence_class,
        "public_reproduction_status": public_reproduction_status,
        "independent_evaluation_status": independent_evaluation_status,
        "findings": sorted(set(findings)),
        "summary": {
            "machine_count": len(records),
            "operator_count": len(operator_ids),
            "os_families": sorted(os_families),
            "distributions": sorted(distributions),
            "architectures": sorted(architectures),
            "semantic_output_digests": sorted(digests),
            "required_machine_labels": sorted(required_labels),
            "missing_machine_labels": missing_labels,
            "result_status": result_status,
            "gate_status": gate_status,
        },
    }
