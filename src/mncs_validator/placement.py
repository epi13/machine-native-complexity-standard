"""Experimental execution-placement evidence validation.

This module validates a bounded observation of resource placement.  It does not
execute a provider, infer correctness, or derive an MNCS/MNCDS conformance result.
"""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .assurance.model import AssuranceValidationReport
from .assurance.status import Status, aggregate_status
from .errors import ManifestError
from .schemas import schema_errors
from .validation import load_json_object

SCHEMA_VERSION = "0.1-experimental"
SCHEMA_NAME = "execution-placement"
_ACCELERATOR_PLACEMENTS = {"full-accelerator", "sequential-offload"}
_PLACEMENTS = _ACCELERATOR_PLACEMENTS | {"cpu-only", "mixed", "unsupported", "indeterminate"}
_TRANSITION_TARGETS = {
    "full-accelerator->sequential-offload": "sequential-offload",
    "sequential-offload->cpu": "cpu-only",
    "full-accelerator->cpu": "cpu-only",
}
_LIMIT_UNITS = {
    "host-memory": "bytes",
    "accelerator-memory": "bytes",
    "accelerator-reserve": "bytes",
    "workspace": "bytes",
    "output": "bytes",
    "timeout": "seconds",
    "concurrency": "count",
}
_MEASUREMENT_UNITS = {
    "peak-accelerator-allocated-bytes": "bytes",
    "peak-accelerator-reserved-bytes": "bytes",
    "process-rss-bytes": "bytes",
    "host-memory-peak-bytes": "bytes",
    "model-storage-bytes": "bytes",
    "workspace-peak-bytes": "bytes",
    "transfer-bytes": "bytes",
    "offload-count": "count",
    "duration-seconds": "seconds",
    "output-bytes": "bytes",
    "maximum-concurrency": "count",
}
_LIMIT_METRICS = {
    "host-memory": {"process-rss-bytes", "host-memory-peak-bytes"},
    "accelerator-memory": {
        "peak-accelerator-allocated-bytes",
        "peak-accelerator-reserved-bytes",
    },
    "workspace": {"workspace-peak-bytes"},
    "output": {"output-bytes"},
    "timeout": {"duration-seconds"},
    "concurrency": {"maximum-concurrency"},
}
_IDENTITY_KEYS = {
    "subject": "subject_id",
    "artifact": "artifact_id",
    "provider": "provider_id",
    "executable": "executable_id",
    "runtime": "runtime_id",
    "environment": "environment_id",
}


def _report(value: dict[str, Any], target: str) -> AssuranceValidationReport:
    report = AssuranceValidationReport(target=target, kind=SCHEMA_NAME)
    report.record_id = value.get("record_id") if isinstance(value.get("record_id"), str) else None
    for error in schema_errors(value, SCHEMA_NAME):
        report.add("SCHEMA", error)
    return report


def _status_match(
    report: AssuranceValidationReport,
    declared: object,
    computed: Status,
    code: str,
    path: str,
) -> None:
    if declared != computed:
        report.add(code, f"declares {declared!r}, expected {computed}", path)


def _identity_status(value: dict[str, Any], report: AssuranceValidationReport) -> None:
    identities = value["identities"]
    bindings = value["identity_bindings"]
    for role, key in _IDENTITY_KEYS.items():
        binding = bindings[role]
        expected = identities[key]
        if binding["declared"] != expected:
            report.add(
                "STALE-IDENTITY-LINK",
                f"{role} binding does not reference the record identity",
                f"$/identity_bindings/{role}/declared",
            )
        if binding["observed"] != binding["declared"]:
            report.add(
                "STALE-IDENTITY-LINK",
                f"{role} identity changed between declaration and observation",
                f"$/identity_bindings/{role}/observed",
            )


def _policy_status(value: dict[str, Any], report: AssuranceValidationReport) -> None:
    policy = value["requested_policy"]
    if policy["limits"] != value["resource_policy"]["limits"]:
        report.add(
            "RESOURCE-POLICY-MISMATCH",
            "requested resource limits differ from the observed resource policy",
            "$/resource_policy/limits",
        )
    mode = policy["mode"]
    actual = value["actual_execution"]["placement"]
    if mode == "cpu" and actual in _ACCELERATOR_PLACEMENTS | {"mixed"}:
        report.add(
            "REQUESTED-PLACEMENT-VIOLATED", "explicit CPU policy observed accelerator execution"
        )
    if mode == "accelerator" and actual not in {"full-accelerator", "indeterminate", "unsupported"}:
        report.add(
            "REQUESTED-PLACEMENT-VIOLATED",
            "explicit accelerator policy did not observe full accelerator placement",
        )
    if mode == "sequential-offload" and actual not in {
        "sequential-offload",
        "indeterminate",
        "unsupported",
    }:
        report.add(
            "REQUESTED-PLACEMENT-VIOLATED",
            "explicit sequential-offload policy did not observe sequential offload",
        )
    if mode != "auto" and value["fallback"]["observed_transitions"]:
        report.add(
            "EXPLICIT-FALLBACK-FORBIDDEN",
            "explicit placement policy silently used a fallback transition",
        )
    backend = policy["backend"]
    observed_backend = value["actual_execution"]["backend"]
    if backend is not None and observed_backend is not None and backend != observed_backend:
        report.add(
            "REQUESTED-BACKEND-VIOLATED", "observed backend differs from explicit policy backend"
        )


def _fallback_status(value: dict[str, Any], report: AssuranceValidationReport) -> None:
    fallback = value["fallback"]
    allowed = set(fallback["allowed_transitions"])
    observed = fallback["observed_transitions"]
    for index, transition in enumerate(observed):
        if transition not in allowed:
            report.add(
                "FALLBACK-NOT-AUTHORIZED",
                f"observed transition {transition!r} was not declared as allowed",
                f"$/fallback/observed_transitions/{index}",
            )
    if observed and not fallback["transition_authorized"]:
        report.add(
            "FALLBACK-NOT-AUTHORIZED", "observed fallback transitions were not policy-authorized"
        )
    if observed:
        actual = value["actual_execution"]["placement"]
        if _TRANSITION_TARGETS[observed[-1]] != actual:
            report.add(
                "FALLBACK-FINAL-PLACEMENT-MISMATCH",
                "the observed fallback chain does not terminate at actual placement",
                "$/actual_execution/placement",
            )


def _capability_status(value: dict[str, Any], report: AssuranceValidationReport) -> None:
    actual = value["actual_execution"]["placement"]
    observations = value["capability_observations"]
    if actual in _ACCELERATOR_PLACEMENTS:
        if observations["discovered"] not in {"available", "unknown"}:
            report.add(
                "ACCELERATOR-NOT-DISCOVERED",
                "accelerator placement requires an available discovered accelerator",
            )
        if observations["execution_probe"] == "FAIL":
            report.add(
                "ACCELERATOR-PROBE-MISSING",
                "accelerator placement requires a successful runtime execution probe",
                "$/capability_observations/execution_probe",
            )


def _precision_status(value: dict[str, Any], report: AssuranceValidationReport) -> None:
    precision = value["precision"]
    requested = precision["requested"]
    effective = precision["effective"]
    if requested not in {"auto", "unknown"} and requested != effective:
        report.add(
            "PRECISION-POLICY-VIOLATED",
            "effective precision differs from an explicit precision request",
        )
    reduced = effective in {"float16", "bfloat16", "int8"}
    if reduced and precision["probe_required"] and precision["probe_status"] == "FAIL":
        report.add(
            "PRECISION-PROBE-MISSING",
            "reduced precision is not verified by its required execution probe",
            "$/precision/probe_status",
        )


def _governing_result_status(value: dict[str, Any], report: AssuranceValidationReport) -> None:
    governing = value.get("governing_results")
    if not isinstance(governing, dict):
        return
    for family, result in governing.items():
        if not isinstance(result, dict):
            continue
        if result["record_id"] == value["record_id"]:
            report.add(
                "GOVERNING-RESULT-SELF-REFERENCE",
                f"{family} result cannot be established by the placement record itself",
                f"$/governing_results/{family}/record_id",
            )


def _residency_status(value: dict[str, Any], report: AssuranceValidationReport) -> None:
    placement = value["actual_execution"]["placement"]
    weights = value["residency"]["weight_placement"]
    if placement == "sequential-offload" and weights == "accelerator":
        report.add(
            "RESIDENCY-CONTRADICTION",
            "sequential offload cannot claim permanent accelerator weight residency",
            "$/residency/weight_placement",
        )
    if placement == "cpu-only" and weights in {"accelerator", "transient-accelerator"}:
        report.add(
            "RESIDENCY-CONTRADICTION",
            "CPU-only placement cannot claim accelerator weight residency",
            "$/residency/weight_placement",
        )
    if placement == "full-accelerator" and weights == "host-ram":
        report.add(
            "RESIDENCY-CONTRADICTION",
            "full accelerator placement cannot claim host-only weight residency",
            "$/residency/weight_placement",
        )


def _known_ids(value: dict[str, Any]) -> set[str]:
    identities = value["identities"]
    references = value["references"]
    return {
        *identities.values(),
        *(item for item in references.values() if isinstance(item, str)),
    }


def _measurement_status(
    value: dict[str, Any], report: AssuranceValidationReport
) -> dict[str, list[float]]:
    measurements = value["measurements"]
    known = _known_ids(value)
    by_metric: dict[str, list[float]] = {}
    for index, item in enumerate(measurements):
        metric = item["metric"]
        if item["unit"] != _MEASUREMENT_UNITS[metric]:
            report.add(
                "MEASUREMENT-UNIT-MISMATCH",
                f"{metric} requires unit {_MEASUREMENT_UNITS[metric]}",
                f"$/measurements/{index}/unit",
            )
        if item["source_id"] not in known:
            report.add(
                "STALE-MEASUREMENT-SOURCE",
                "measurement source is not bound to an observed identity",
                f"$/measurements/{index}/source_id",
            )
        number = item["value"]
        if not isinstance(number, (int, float)) or not math.isfinite(float(number)):
            report.add(
                "NONFINITE-MEASUREMENT",
                "measurement values must be finite",
                f"$/measurements/{index}/value",
            )
        else:
            by_metric.setdefault(metric, []).append(float(number))
    return by_metric


def _resource_status(
    value: dict[str, Any],
    report: AssuranceValidationReport,
    by_metric: dict[str, list[float]],
) -> Status:
    limits = value["resource_policy"]["limits"]
    statuses: list[Status] = []
    for index, limit in enumerate(limits):
        resource = limit["resource"]
        if limit["unit"] != _LIMIT_UNITS[resource]:
            report.add(
                "RESOURCE-LIMIT-UNIT",
                f"{resource} requires unit {_LIMIT_UNITS[resource]}",
                f"$/resource_policy/limits/{index}/unit",
            )
        metrics = _LIMIT_METRICS.get(resource, set())
        observed = [number for metric in metrics for number in by_metric.get(metric, [])]
        if not observed:
            statuses.append("UNKNOWN")
            continue
        if any(number > limit["value"] for number in observed):
            statuses.append("FAIL")
        else:
            statuses.append("PASS")
    return aggregate_status(statuses)


def _placement_status(value: dict[str, Any]) -> Status:
    actual = value["actual_execution"]
    placement = actual["placement"]
    if placement in {"unsupported", "indeterminate"}:
        return "UNKNOWN"
    if actual["status"] == "FAIL":
        return "UNKNOWN"
    evidence = value["placement_evidence"]
    matching = [
        item
        for item in evidence
        if item["status"] == "PASS" and item["observed_placement"] == placement
    ]
    if placement == "sequential-offload":
        matching = [
            item
            for item in matching
            if item["kind"]
            in {"runtime-hook", "parameter-device-state", "provider-witness", "runtime-measurement"}
        ]
    if not matching:
        return "UNKNOWN"
    if (
        placement in _ACCELERATOR_PLACEMENTS
        and value["capability_observations"]["execution_probe"] != "PASS"
    ):
        return "UNKNOWN"
    precision = value["precision"]
    if (
        precision["effective"] in {"float16", "bfloat16", "int8"}
        and precision["probe_required"]
        and precision["probe_status"] != "PASS"
    ):
        return "UNKNOWN"
    return "PASS"


def validate_placement_value(
    value: dict[str, Any], *, target: str = "$"
) -> AssuranceValidationReport:
    """Validate one placement record without executing or generalizing it."""

    report = _report(value, target)
    if not report.valid:
        report.computed_status = "UNKNOWN"
        return report
    _identity_status(value, report)
    _policy_status(value, report)
    _governing_result_status(value, report)
    _fallback_status(value, report)
    _capability_status(value, report)
    _precision_status(value, report)
    _residency_status(value, report)
    by_metric = _measurement_status(value, report)

    actual_execution = value["actual_execution"]["status"]
    placement = _placement_status(value)
    resources = _resource_status(value, report, by_metric)
    computed = aggregate_status([actual_execution, placement, resources])
    report.rule_results = {
        "MNCS-EXP-PLACEMENT-EXECUTION": actual_execution,
        "MNCS-EXP-PLACEMENT-EVIDENCE": placement,
        "MNCS-EXP-PLACEMENT-RESOURCES": resources,
    }
    report.computed_status = computed
    results = value["results"]
    _status_match(
        report, results["execution"], actual_execution, "RESULT-MISMATCH", "$/results/execution"
    )
    _status_match(report, results["placement"], placement, "RESULT-MISMATCH", "$/results/placement")
    _status_match(
        report,
        results["resource_policy"],
        resources,
        "RESULT-MISMATCH",
        "$/results/resource_policy",
    )
    _status_match(report, results["status"], computed, "RESULT-MISMATCH", "$/results/status")
    return report


def validate_placement_file(path: Path) -> AssuranceValidationReport:
    """Load and validate one strict JSON placement record."""

    try:
        value = load_json_object(path)
    except ManifestError as exc:
        report = AssuranceValidationReport(target=str(path), kind=SCHEMA_NAME)
        report.add("INVALID-JSON", str(exc), str(path))
        report.computed_status = "UNKNOWN"
        return report
    version = value.get("schema_version")
    if version != SCHEMA_VERSION:
        report = AssuranceValidationReport(
            target=str(path), kind=SCHEMA_NAME, valid=False, supported=False
        )
        report.add(
            "UNSUPPORTED-VERSION",
            f"unsupported placement schema version: {version!r}",
            "$/schema_version",
        )
        report.computed_status = "UNKNOWN"
        return report
    return validate_placement_value(value, target=str(path))
