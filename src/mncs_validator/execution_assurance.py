"""Offline execution-assurance validation for MNCS and MNCDS test evidence."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from .assurance.status import Status, aggregate_status
from .canonical import canonical_sha256_file
from .schemas import schema_errors
from .validation import load_json_object

SubjectFamily = Literal["MNCS", "MNCDS"]
SubjectKind = Literal["contract", "assurance", "threat", "measurement", "development-record"]

PROPERTY_NAMES = (
    "command_bound",
    "environment_bound",
    "filesystem_isolation",
    "network_isolation",
    "process_isolation",
    "resource_limits",
    "test_integrity",
    "result_integrity",
    "host_root_resistance",
    "protected_custody",
    "independent_operation",
)
LOCAL_ATTESTATION_KINDS = {"none", "local-record", "signed-local"}
NON_EXTERNAL_ATTESTATION_KINDS = LOCAL_ATTESTATION_KINDS | {
    "platform-quote",
    "confidential-vm",
}


@dataclass(frozen=True)
class ExecutionAssuranceIssue:
    """One normalized execution-assurance finding."""

    code: str
    message: str
    path: str = ""


@dataclass
class ExecutionAssuranceReport:
    """Validation and assurance result for one companion execution record."""

    target: str
    valid: bool = True
    supported: bool = True
    test_status: Status = "UNKNOWN"
    assurance_status: Status = "PASS"
    combined_status: Status = "UNKNOWN"
    record_id: str | None = None
    subject_identity: str | None = None
    property_results: dict[str, Status] = field(default_factory=dict)
    issues: list[ExecutionAssuranceIssue] = field(default_factory=list)
    warnings: list[ExecutionAssuranceIssue] = field(default_factory=list)

    @property
    def category(self) -> str:
        if not self.supported:
            return "UNSUPPORTED"
        if not self.valid:
            return "INVALID"
        return self.combined_status

    def invalidate(self, code: str, message: str, path: str = "") -> None:
        self.valid = False
        self.assurance_status = "FAIL"
        self.combined_status = "FAIL"
        self.issues.append(ExecutionAssuranceIssue(code, message, path))

    def fail(self, code: str, message: str, path: str = "") -> None:
        self.assurance_status = "FAIL"
        self.warnings.append(ExecutionAssuranceIssue(code, message, path))

    def unknown(self, code: str, message: str, path: str = "") -> None:
        if self.assurance_status != "FAIL":
            self.assurance_status = "UNKNOWN"
        self.warnings.append(ExecutionAssuranceIssue(code, message, path))

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["category"] = self.category
        return result


def parse_evaluation_time(value: str | None) -> datetime:
    """Parse an optional RFC 3339 timestamp for deterministic offline evaluation."""

    if value is None:
        return datetime.now(UTC)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("execution-assurance timestamps must include an RFC 3339 UTC offset")
    return parsed.astimezone(UTC)


def _parse_time(value: str) -> datetime:
    return parse_evaluation_time(value)


def _status(value: object) -> Status:
    if value in {"PASS", "FAIL", "UNKNOWN"}:
        return value
    return "UNKNOWN"


def _semantic_assurance(
    value: dict[str, Any],
    report: ExecutionAssuranceReport,
    *,
    at: datetime,
) -> None:
    execution = cast(dict[str, Any], value["execution"])
    properties = cast(dict[str, Any], execution["properties"])
    report.property_results = {name: _status(properties.get(name)) for name in PROPERTY_NAMES}

    required = cast(list[str], value["required_properties"])
    report.assurance_status = aggregate_status(
        [report.property_results.get(name, "UNKNOWN") for name in required]
    )

    challenge = cast(dict[str, Any], execution["challenge"])
    issued_at = _parse_time(cast(str, challenge["issued_at"]))
    expires_at = _parse_time(cast(str, challenge["expires_at"]))
    if expires_at <= issued_at:
        report.invalidate(
            "challenge-window-invalid",
            "challenge expires_at must be later than issued_at",
            "$/execution/challenge",
        )
        return

    attestation = cast(dict[str, Any], execution["attestation"])
    kind = cast(str, attestation["kind"])
    identity = attestation["identity"]
    signer_id = attestation["signer_id"]
    verified = cast(bool, attestation["verified"])
    fresh = cast(bool, attestation["fresh"])

    if kind == "none":
        if identity is not None or signer_id is not None or verified:
            report.invalidate(
                "attestation-none-contradiction",
                "attestation kind none cannot include an identity, signer, or verified=true",
                "$/execution/attestation",
            )
            return
        report.unknown(
            "attestation-absent",
            "no verified execution attestation is present",
            "$/execution/attestation",
        )
    else:
        if identity is None or signer_id is None:
            report.invalidate(
                "attestation-identity-missing",
                "a declared attestation requires identity and signer_id",
                "$/execution/attestation",
            )
            return
        if not verified:
            report.unknown(
                "attestation-unverified",
                "the declared execution attestation was not verified",
                "$/execution/attestation/verified",
            )
        if not fresh:
            report.fail(
                "attestation-stale",
                "the execution attestation is not fresh",
                "$/execution/attestation/fresh",
            )

    if kind in LOCAL_ATTESTATION_KINDS:
        for name in ("host_root_resistance", "protected_custody", "independent_operation"):
            if report.property_results[name] == "PASS":
                report.fail(
                    "local-attestation-overclaim",
                    f"{kind} cannot establish {name}",
                    f"$/execution/properties/{name}",
                )
    elif kind == "platform-quote":
        for name in ("protected_custody", "independent_operation"):
            if report.property_results[name] == "PASS":
                report.fail(
                    "platform-attestation-overclaim",
                    f"a platform quote alone cannot establish {name}",
                    f"$/execution/properties/{name}",
                )
    elif kind == "confidential-vm":
        for name in ("protected_custody", "independent_operation"):
            if report.property_results[name] == "PASS":
                report.fail(
                    "confidential-vm-overclaim",
                    f"a confidential VM alone cannot establish {name}",
                    f"$/execution/properties/{name}",
                )

    if (
        kind in NON_EXTERNAL_ATTESTATION_KINDS
        and report.property_results["independent_operation"] == "PASS"
    ):
        report.fail(
            "independence-overclaim",
            "organizational independence requires an externally controlled evaluator",
            "$/execution/properties/independent_operation",
        )

    declared = _status(value["declared_assurance_status"])
    if declared != report.assurance_status:
        report.invalidate(
            "assurance-status-mismatch",
            f"declared assurance status {declared} does not match computed "
            f"{report.assurance_status}",
            "$/declared_assurance_status",
        )
        return

    if at < issued_at:
        report.fail(
            "challenge-not-yet-valid",
            "execution challenge was evaluated before it was issued",
            "$/execution/challenge/issued_at",
        )
    if at > expires_at:
        report.fail(
            "challenge-expired",
            "execution challenge is stale and may be replayed",
            "$/execution/challenge/expires_at",
        )


def validate_execution_assurance_value(
    value: dict[str, Any],
    *,
    target: str = "<memory>",
    subject_path: Path | None = None,
    expected_family: SubjectFamily | None = None,
    expected_kind: SubjectKind | None = None,
    expected_test_status: Status | None = None,
    at: datetime | None = None,
) -> ExecutionAssuranceReport:
    """Validate one execution-assurance value without executing any test or provider."""

    report = ExecutionAssuranceReport(target=target)
    if value.get("schema_version") != "0.1":
        report.supported = False
        report.valid = False
        report.assurance_status = "UNKNOWN"
        report.combined_status = "UNKNOWN"
        report.warnings.append(
            ExecutionAssuranceIssue(
                "unsupported-schema-version",
                f"unsupported execution-assurance schema version: {value.get('schema_version')!r}",
                "$/schema_version",
            )
        )
        return report

    errors = schema_errors(value, "execution-assurance-0.1")
    if errors:
        for error in errors:
            report.invalidate("schema", error)
        return report

    report.record_id = cast(str, value["record_id"])
    subject = cast(dict[str, Any], value["subject"])
    report.test_status = _status(cast(dict[str, Any], value["test_result"])["status"])
    report.subject_identity = cast(str, subject["canonical_sha256"])

    if at is not None and (at.tzinfo is None or at.utcoffset() is None):
        raise ValueError("execution-assurance evaluation time must include a UTC offset")
    evaluation_time = datetime.now(UTC) if at is None else at.astimezone(UTC)
    _semantic_assurance(value, report, at=evaluation_time)

    if report.valid and expected_family is not None and subject["family"] != expected_family:
        report.invalidate(
            "subject-family-mismatch",
            f"expected {expected_family} execution evidence, found {subject['family']}",
            "$/subject/family",
        )
    if report.valid and expected_kind is not None and subject["kind"] != expected_kind:
        report.invalidate(
            "subject-kind-mismatch",
            f"expected subject kind {expected_kind}, found {subject['kind']}",
            "$/subject/kind",
        )
    if (
        report.valid
        and expected_test_status is not None
        and report.test_status != expected_test_status
    ):
        report.invalidate(
            "test-status-mismatch",
            f"execution record reports {report.test_status}, subject validator computed "
            f"{expected_test_status}",
            "$/test_result/status",
        )

    if report.valid and subject_path is not None:
        report.subject_identity = canonical_sha256_file(subject_path)
        if report.subject_identity != subject["canonical_sha256"]:
            report.fail(
                "subject-identity-mismatch",
                "execution assurance is bound to a different canonical subject record",
                "$/subject/canonical_sha256",
            )

    report.combined_status = aggregate_status([report.test_status, report.assurance_status])
    if not report.valid:
        report.combined_status = "FAIL"
    return report


def validate_execution_assurance_file(
    path: Path,
    *,
    subject_path: Path | None = None,
    expected_family: SubjectFamily | None = None,
    expected_kind: SubjectKind | None = None,
    expected_test_status: Status | None = None,
    at: datetime | None = None,
) -> ExecutionAssuranceReport:
    """Load and validate one bounded execution-assurance JSON file."""

    value = load_json_object(path)
    return validate_execution_assurance_value(
        value,
        target=str(path),
        subject_path=subject_path,
        expected_family=expected_family,
        expected_kind=expected_kind,
        expected_test_status=expected_test_status,
        at=at,
    )
