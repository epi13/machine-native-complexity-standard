"""Validation for the experimental runner-produced execution receipt.

Receipts describe observations made by the runner.  They do not establish
correctness, conformance, isolation, custody, independence, or promotion.
"""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from .assurance.status import Status
from .canonical import canonical_sha256
from .schemas import schema_errors
from .validation import load_json_object

SCHEMA_NAME = "execution-receipt-0.1-experimental"
SCHEMA_VERSION = "0.1-experimental"
_METRIC_UNITS = {
    "wall-duration": "seconds",
    "cpu-time": "seconds",
    "process-rss-peak": "bytes",
    "host-memory-peak": "bytes",
    "accelerator-allocated-peak": "bytes",
    "accelerator-reserved-peak": "bytes",
    "process-count": "count",
    "output-bytes": "bytes",
    "transfer-bytes": "bytes",
    "offload-count": "count",
}
_LIMIT_UNITS = {
    "timeout": "seconds",
    "output": "bytes",
    "host-memory": "bytes",
    "accelerator-memory": "bytes",
    "workspace": "bytes",
    "concurrency": "count",
}
_ENFORCEMENT_TO_ASSURANCE = {
    "command_bound": "command_binding",
    "environment_bound": "environment_binding",
    "filesystem_isolation": "filesystem_restriction",
    "network_isolation": "network_restriction",
    "process_isolation": "process_restriction",
    "resource_limits": "resource_limits",
    "test_integrity": "test_bundle_integrity",
    "result_integrity": "result_integrity",
}


@dataclass(frozen=True)
class ExecutionReceiptIssue:
    code: str
    message: str
    path: str = ""


@dataclass
class ExecutionReceiptReport:
    """Offline receipt report; process outcome and validation are separate."""

    target: str
    valid: bool = True
    supported: bool = True
    validation_status: Status = "PASS"
    execution_status: Status = "UNKNOWN"
    harness_status: Status = "UNKNOWN"
    record_id: str | None = None
    receipt_identity: str | None = None
    issues: list[ExecutionReceiptIssue] = field(default_factory=list)
    warnings: list[ExecutionReceiptIssue] = field(default_factory=list)

    @property
    def category(self) -> str:
        if not self.supported:
            return "UNSUPPORTED"
        if not self.valid:
            return "INVALID"
        return self.validation_status

    def invalidate(self, code: str, message: str, path: str = "") -> None:
        self.valid = False
        self.validation_status = "FAIL"
        self.issues.append(ExecutionReceiptIssue(code, message, path))

    def unknown(self, code: str, message: str, path: str = "") -> None:
        if self.validation_status != "FAIL":
            self.validation_status = "UNKNOWN"
        self.warnings.append(ExecutionReceiptIssue(code, message, path))

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["category"] = self.category
        return result


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("execution receipt timestamps must include an RFC 3339 UTC offset")
    return parsed.astimezone(UTC)


def _receipt_digest(value: dict[str, Any]) -> str:
    material = deepcopy(value)
    material.pop("receipt_identity", None)
    return canonical_sha256(material)


def _semantic(value: dict[str, Any], report: ExecutionReceiptReport) -> None:
    subject = cast(dict[str, Any], value["subject"])
    bundle = cast(dict[str, Any], value["bundle"])
    policy = cast(dict[str, Any], value["policy"])
    runner = cast(dict[str, Any], value["runner"])
    environment = cast(dict[str, Any], value["environment"])
    challenge = cast(dict[str, Any], value["challenge"])
    request = cast(dict[str, Any], value["request"])
    lifecycle = cast(dict[str, Any], value["lifecycle"])
    process = cast(dict[str, Any], value["process"])

    report.record_id = cast(str, value["record_id"])
    report.receipt_identity = cast(str, value["receipt_identity"])
    if report.receipt_identity != _receipt_digest(value):
        report.invalidate(
            "receipt-identity-mismatch",
            "receipt_identity is not the canonical SHA-256 of the receipt without receipt_identity",
            "$/receipt_identity",
        )

    try:
        issued = _time(cast(str, challenge["issued_at"]))
        expires = _time(cast(str, challenge["expires_at"]))
        observed = _time(cast(str, request["observed_at"]))
        started = _time(cast(str, lifecycle["started_at"])) if lifecycle["started_at"] else None
        ended = _time(cast(str, lifecycle["ended_at"])) if lifecycle["ended_at"] else None
    except ValueError as exc:
        report.invalidate("timestamp-invalid", str(exc), "$/challenge")
        return

    if expires <= issued:
        report.invalidate(
            "challenge-window-invalid",
            "challenge expires_at must be later than issued_at",
            "$/challenge",
        )
    if observed < issued or observed > expires:
        report.invalidate(
            "challenge-observation-outside-window",
            "request observation is outside the challenge window",
            "$/request/observed_at",
        )
    if started is not None and started < issued:
        report.invalidate(
            "execution-before-challenge",
            "execution started before challenge issuance",
            "$/lifecycle/started_at",
        )
    if ended is not None and ended < issued:
        report.invalidate(
            "execution-before-challenge",
            "execution ended before challenge issuance",
            "$/lifecycle/ended_at",
        )
    if started is not None and ended is not None and ended < started:
        report.invalidate(
            "lifecycle-order-invalid", "ended_at must not precede started_at", "$/lifecycle"
        )
    if started is not None and ended is not None and ended > expires:
        report.invalidate(
            "challenge-expired-during-execution",
            "execution ended after challenge expiry",
            "$/lifecycle/ended_at",
        )

    if request["status"] == "accepted" and (started is None or ended is None):
        report.unknown(
            "incomplete-receipt",
            "an accepted request must include start and end observations",
            "$/lifecycle",
        )
    if request["status"] == "rejected" and (started is not None or ended is not None):
        report.invalidate(
            "rejected-request-ran",
            "a rejected request cannot contain execution lifecycle timestamps",
            "$/request",
        )

    category = cast(str, lifecycle["termination_category"])
    exit_code = process["exit_code"]
    signal = process["signal"]
    if category == "completed" and exit_code != 0:
        report.invalidate(
            "completion-exit-contradiction",
            "completed execution must have exit_code 0",
            "$/process/exit_code",
        )
    if category == "nonzero-exit" and (not isinstance(exit_code, int) or exit_code == 0):
        report.invalidate(
            "nonzero-exit-missing",
            "nonzero-exit requires a nonzero exit_code",
            "$/process/exit_code",
        )
    if category in {"signal", "crash"} and signal is None:
        report.invalidate(
            "signal-observation-missing",
            f"{category} requires a signal observation",
            "$/process/signal",
        )
    termination = cast(dict[str, Any], value["termination_observations"])
    if category == "timeout" and termination["timeout_seconds"] is None:
        report.invalidate(
            "timeout-observation-missing",
            "timeout termination requires timeout_seconds",
            "$/termination_observations/timeout_seconds",
        )
    if category == "resource-limit" and termination["resource_name"] is None:
        report.invalidate(
            "resource-observation-missing",
            "resource-limit termination requires resource_name",
            "$/termination_observations/resource_name",
        )
    if category == "output-limit":
        streams = cast(dict[str, Any], value["streams"])
        aggregate = cast(dict[str, Any], value["aggregate_output"])
        if not aggregate["limit_hit"] and not any(
            streams[name]["limit_hit"] for name in ("stdout", "stderr")
        ):
            report.invalidate(
                "output-limit-observation-missing",
                "output-limit termination requires a stream or aggregate limit_hit",
                "$/aggregate_output/limit_hit",
            )
    if request["status"] == "rejected" and category != "policy-rejected":
        report.invalidate(
            "rejection-termination-mismatch",
            "rejected requests must use policy-rejected termination",
            "$/lifecycle/termination_category",
        )

    report.harness_status = cast(Status, process["harness_status"])
    artifacts = cast(list[dict[str, Any]], value["artifacts"])
    if process["result_identity"] is not None and not any(
        artifact["identity"] == process["result_identity"] for artifact in artifacts
    ):
        report.invalidate(
            "result-artifact-mismatch",
            "process result_identity is not present in retained result artifacts",
            "$/process/result_identity",
        )
    if category == "completed" and exit_code == 0:
        report.execution_status = "PASS"
    elif category in {
        "nonzero-exit",
        "timeout",
        "signal",
        "crash",
        "resource-limit",
        "output-limit",
        "cancelled",
        "internal-runner-error",
        "policy-rejected",
    }:
        report.execution_status = "FAIL"
    else:
        report.execution_status = "UNKNOWN"

    streams = cast(dict[str, Any], value["streams"])
    for name in ("stdout", "stderr"):
        stream = streams[name]
        if stream["retained_bytes"] > stream["total_bytes"]:
            report.invalidate(
                "retained-bytes-exceed-total",
                f"{name} retained_bytes exceeds total_bytes",
                f"$/streams/{name}",
            )
        if stream["truncated"] != (stream["retained_bytes"] < stream["total_bytes"]):
            report.invalidate(
                "truncation-contradiction",
                f"{name} truncated does not match retained and total bytes",
                f"$/streams/{name}/truncated",
            )
        if stream["limit_hit"] and stream["limit_bytes"] is None:
            report.invalidate(
                "stream-limit-missing",
                f"{name} limit_hit requires limit_bytes",
                f"$/streams/{name}/limit_bytes",
            )
    aggregate = cast(dict[str, Any], value["aggregate_output"])
    if aggregate["retained_bytes"] > aggregate["total_bytes"]:
        report.invalidate(
            "aggregate-retained-bytes-exceed-total",
            "aggregate retained_bytes exceeds total_bytes",
            "$/aggregate_output",
        )
    if aggregate["limit_hit"] and aggregate["limit_bytes"] is None:
        report.invalidate(
            "aggregate-limit-missing",
            "aggregate limit_hit requires limit_bytes",
            "$/aggregate_output/limit_bytes",
        )

    for index, limit in enumerate(cast(list[dict[str, Any]], policy["requested_limits"])):
        if _LIMIT_UNITS[limit["resource"]] != limit["unit"]:
            report.invalidate(
                "resource-limit-unit-invalid",
                "resource limit unit does not match resource",
                f"$/policy/requested_limits/{index}/unit",
            )
    for index, observation in enumerate(cast(list[dict[str, Any]], value["resources"])):
        if _METRIC_UNITS[observation["metric"]] != observation["unit"]:
            report.invalidate(
                "resource-measurement-unit-invalid",
                "resource measurement unit does not match metric",
                f"$/resources/{index}/unit",
            )

    placement = cast(dict[str, Any], value["placement"])["execution_placement_reference"]
    if placement is not None:
        if placement["subject_identity"] != subject["canonical_sha256"]:
            report.invalidate(
                "placement-subject-stale",
                "placement evidence is bound to a different subject",
                "$/placement/execution_placement_reference/subject_identity",
            )
        if placement["environment_identity"] != environment["environment_identity"]:
            report.invalidate(
                "placement-environment-stale",
                "placement evidence is bound to a different environment",
                "$/placement/execution_placement_reference/environment_identity",
            )

    # These fields are intentionally read so a future adapter cannot turn a raw
    # runner receipt into a broad authority claim by omission.
    _ = bundle, policy, runner


def validate_execution_receipt_value(
    value: dict[str, Any],
    *,
    target: str = "<memory>",
    placement_value: dict[str, Any] | None = None,
) -> ExecutionReceiptReport:
    """Validate one receipt without executing a runner or resolving providers."""

    report = ExecutionReceiptReport(target=target)
    if value.get("schema_version") != SCHEMA_VERSION:
        report.supported = False
        report.validation_status = "UNKNOWN"
        report.warnings.append(
            ExecutionReceiptIssue(
                "unsupported-schema-version",
                f"unsupported execution-receipt schema version: {value.get('schema_version')!r}",
                "$/schema_version",
            )
        )
        return report
    errors = schema_errors(value, SCHEMA_NAME)
    if errors:
        for error in errors:
            report.invalidate("schema", error)
        return report
    _semantic(value, report)
    if placement_value is not None:
        from .placement import validate_placement_value

        placement = cast(dict[str, Any], value["placement"])["execution_placement_reference"]
        placement_report = validate_placement_value(placement_value, target=f"{target}:placement")
        if not placement_report.valid or placement_report.category == "UNKNOWN":
            report.unknown(
                "placement-evidence-unknown",
                "referenced placement evidence is not sufficient",
                "$/placement/execution_placement_reference",
            )
        elif (
            placement is None
            or placement["record_id"] != placement_value.get("record_id")
            or placement["identity"] != canonical_sha256(placement_value)
            or placement["environment_identity"]
            != placement_value.get("identities", {}).get("environment_id")
        ):
            report.invalidate(
                "placement-reference-mismatch",
                "receipt placement reference does not match supplied placement evidence",
                "$/placement/execution_placement_reference",
            )
    elif value["placement"]["execution_placement_reference"] is not None:
        report.unknown(
            "placement-reference-unresolved",
            "placement reference was not resolved by this offline validation",
            "$/placement/execution_placement_reference",
        )
    return report


def validate_execution_receipt_file(
    path: Path, *, placement_path: Path | None = None, bundle_path: Path | None = None
) -> ExecutionReceiptReport:
    """Load and validate one bounded receipt JSON file."""

    value = load_json_object(path)
    placement = load_json_object(placement_path) if placement_path is not None else None
    report = validate_execution_receipt_value(value, target=str(path), placement_value=placement)
    if bundle_path is not None:
        from .execution_bundle import bind_receipt_to_bundle, verify_execution_bundle_archive

        bundle_report = verify_execution_bundle_archive(bundle_path)
        if not bundle_report.valid:
            report.invalidate(
                "bundle-invalid",
                "supplied execution bundle did not verify",
                str(bundle_path),
            )
        binding = bind_receipt_to_bundle(value, bundle_report, target=f"{path}:bundle")
        for issue in binding.issues:
            report.invalidate(issue.code, issue.message, issue.path)
    return report


def validate_execution_receipt_binding(
    assurance: dict[str, Any], receipt: dict[str, Any], *, target: str = "<binding>"
) -> ExecutionReceiptReport:
    """Check that assurance facts are exactly bound to a validated receipt."""

    report = validate_execution_receipt_value(receipt, target=f"{target}:receipt")
    reference = assurance.get("execution_receipt")
    if not isinstance(reference, dict):
        report.invalidate(
            "receipt-reference-missing",
            "assurance record does not reference the supplied receipt",
            "$/execution_receipt",
        )
        return report
    if reference.get("record_id") != receipt.get("record_id") or reference.get(
        "identity"
    ) != receipt.get("receipt_identity"):
        report.invalidate(
            "receipt-reference-mismatch",
            "assurance receipt reference does not match the supplied receipt",
            "$/execution_receipt",
        )
    subject_a = cast(dict[str, Any], assurance.get("subject", {}))
    subject_r = cast(dict[str, Any], receipt.get("subject", {}))
    for key in ("family", "kind", "record_id", "canonical_sha256", "candidate_id"):
        if subject_a.get(key) != subject_r.get(key):
            report.invalidate(
                "receipt-subject-mismatch",
                f"receipt subject {key} does not match assurance",
                f"$/subject/{key}",
            )
    test_a = cast(dict[str, Any], assurance.get("test_result", {}))
    process_r = cast(dict[str, Any], receipt.get("process", {}))
    for key_a, key_r in (("status", "harness_status"), ("result_identity", "result_identity")):
        if test_a.get(key_a) != process_r.get(key_r):
            report.invalidate(
                "receipt-result-mismatch",
                f"receipt result {key_a} does not match assurance",
                f"$/test_result/{key_a}",
            )
    execution_a = cast(dict[str, Any], assurance.get("execution", {}))
    for key_a, key_r in (
        ("test_bundle_identity", "test_bundle_identity"),
        ("policy_identity", "execution_policy_identity"),
        ("runner_identity", "runner_identity"),
        ("environment_identity", "environment_identity"),
    ):
        actual = (
            receipt["bundle"]["test_bundle_identity"]
            if key_r == "test_bundle_identity"
            else receipt["policy"][key_r]
            if key_r == "execution_policy_identity"
            else receipt["runner"][key_r]
            if key_r == "runner_identity"
            else receipt["environment"][key_r]
        )
        if execution_a.get(key_a) != actual:
            report.invalidate(
                "receipt-execution-binding-mismatch",
                f"receipt {key_a} does not match assurance",
                f"$/execution/{key_a}",
            )
    challenge_a = cast(dict[str, Any], execution_a.get("challenge", {}))
    challenge_r = cast(dict[str, Any], receipt.get("challenge", {}))
    for key in ("nonce", "issued_at", "expires_at"):
        if challenge_a.get(key) != challenge_r.get(key):
            report.invalidate(
                "receipt-challenge-mismatch",
                f"receipt challenge {key} does not match assurance",
                f"$/execution/challenge/{key}",
            )
    properties_a = cast(dict[str, Any], execution_a.get("properties", {}))
    enforcement_r = cast(dict[str, Any], receipt.get("enforcement", {}))
    for assurance_name, receipt_name in _ENFORCEMENT_TO_ASSURANCE.items():
        if (
            properties_a.get(assurance_name) == "PASS"
            and enforcement_r.get(receipt_name) != "enforced"
        ):
            report.invalidate(
                "receipt-enforcement-overclaim",
                f"assurance claims {assurance_name}=PASS but receipt does not report enforcement",
                f"$/execution/properties/{assurance_name}",
            )
    return report
