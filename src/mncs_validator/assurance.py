"""Offline MNCS 0.3 release-candidate record validation."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, cast

from .errors import ManifestError
from .schemas import schema_errors
from .validation import load_json_object

Status = Literal["PASS", "FAIL", "UNKNOWN"]
RecordKind = Literal["contract", "assurance", "threat", "measurement"]

STATUS_ORDER: dict[str, int] = {"PASS": 0, "UNKNOWN": 1, "FAIL": 2}
SCHEMAS: dict[RecordKind, str] = {
    "contract": "contract-profile-0.3",
    "assurance": "assurance-case-0.3",
    "threat": "threat-record-0.3",
    "measurement": "measurement-profile-0.3",
}


@dataclass(frozen=True)
class AssuranceIssue:
    """One normalized release-candidate finding."""

    code: str
    message: str
    path: str = ""


@dataclass
class AssuranceValidationReport:
    """Schema, semantic, and conformance outcome for one RC record."""

    target: str
    kind: str
    valid: bool = True
    supported: bool = True
    computed_status: Status = "PASS"
    record_id: str | None = None
    issues: list[AssuranceIssue] = field(default_factory=list)
    warnings: list[AssuranceIssue] = field(default_factory=list)
    rule_results: dict[str, Status] = field(default_factory=dict)

    @property
    def category(self) -> str:
        if not self.supported:
            return "UNSUPPORTED"
        if not self.valid:
            return "INVALID"
        return self.computed_status

    def add(self, code: str, message: str, path: str = "") -> None:
        self.valid = False
        self.issues.append(AssuranceIssue(code, message, path))

    def warn(self, code: str, message: str, path: str = "") -> None:
        self.warnings.append(AssuranceIssue(code, message, path))

    def rule(self, code: str, status: Status, message: str = "", path: str = "") -> None:
        self.rule_results[code] = status
        self.computed_status = aggregate_status([self.computed_status, status])
        if status != "PASS" and message:
            self.warn(code, message, path)

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["category"] = self.category
        return result


def aggregate_status(statuses: Sequence[str]) -> Status:
    """Apply FAIL > UNKNOWN > PASS; invalid or missing values remain UNKNOWN."""

    if not statuses or any(status not in STATUS_ORDER for status in statuses):
        return "UNKNOWN"
    return cast(Status, max(statuses, key=STATUS_ORDER.__getitem__))


def _objects(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [cast(dict[str, Any], item) for item in value if isinstance(item, dict)]


def _strings(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _freshness_status(value: object, at: datetime | None) -> Status:
    if not isinstance(value, dict):
        return "UNKNOWN"
    declared = value.get("status")
    status = declared if isinstance(declared, str) and declared in STATUS_ORDER else "UNKNOWN"
    valid_until = _parse_time(value.get("valid_until"))
    if at is not None and valid_until is not None and at > valid_until:
        return aggregate_status([status, "UNKNOWN"])
    return cast(Status, status)


def _schema_report(
    value: dict[str, Any],
    kind: RecordKind,
    target: str,
) -> AssuranceValidationReport:
    report = AssuranceValidationReport(target=target, kind=kind)
    identity_keys = {
        "contract": "profile_id",
        "assurance": "assurance_case_id",
        "threat": "threat_id",
        "measurement": "profile_id",
    }
    identity = value.get(identity_keys[kind])
    report.record_id = identity if isinstance(identity, str) else None
    for error in schema_errors(value, SCHEMAS[kind]):
        report.add("SCHEMA", error)
    return report


def validate_contract_value(
    value: dict[str, Any],
    *,
    target: str = "$",
) -> AssuranceValidationReport:
    """Validate contract adequacy without evaluating the candidate."""

    report = _schema_report(value, "contract", target)
    if not report.valid:
        return report

    statuses = [
        str(finding.get("status"))
        for finding in _objects(value.get("findings"))
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

    for ambiguity in _objects(value.get("ambiguities")):
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


def _unique_map(
    values: list[dict[str, Any]],
    key: str,
    report: AssuranceValidationReport,
    path: str,
    code: str,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(values):
        identity = item.get(key)
        if not isinstance(identity, str):
            continue
        if identity in result:
            report.add(code, f"duplicate identity: {identity}", f"{path}/{index}/{key}")
        result[identity] = item
    return result


def _claim_cycles(
    claim_ids: set[str],
    dependencies: list[dict[str, Any]],
    report: AssuranceValidationReport,
) -> None:
    graph: dict[str, list[str]] = {claim_id: [] for claim_id in claim_ids}
    for dependency in dependencies:
        source = dependency.get("source_claim_id")
        target = dependency.get("target_claim_id")
        if isinstance(source, str) and isinstance(target, str) and source in graph:
            graph[source].append(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(claim_id: str) -> None:
        if claim_id in visited:
            return
        if claim_id in visiting:
            report.add(
                "MNCS-03-DEPENDENCY-CYCLE",
                f"claim dependency cycle includes {claim_id}",
            )
            return
        visiting.add(claim_id)
        for target in graph.get(claim_id, []):
            if target in graph:
                visit(target)
        visiting.remove(claim_id)
        visited.add(claim_id)

    for claim_id in sorted(graph):
        visit(claim_id)


def _derive_claim_statuses(
    claims: dict[str, dict[str, Any]],
    dependencies: list[dict[str, Any]],
    groups: dict[str, dict[str, Any]],
    at: datetime | None,
) -> dict[str, Status]:
    outgoing: dict[str, list[dict[str, Any]]] = {claim_id: [] for claim_id in claims}
    for dependency in dependencies:
        source = dependency.get("source_claim_id")
        if isinstance(source, str) and source in outgoing:
            outgoing[source].append(dependency)
    derived: dict[str, Status] = {}
    visiting: set[str] = set()

    def derive(claim_id: str) -> Status:
        if claim_id in derived:
            return derived[claim_id]
        if claim_id in visiting:
            return "UNKNOWN"
        visiting.add(claim_id)
        claim = claims[claim_id]
        statuses = [
            str(claim.get("base_status", "UNKNOWN")),
            _freshness_status(claim.get("freshness"), at),
        ]
        if claim.get("retired") is True:
            statuses.append("FAIL")
        for dependency in outgoing[claim_id]:
            if dependency.get("required") is not True:
                continue
            target = dependency.get("target_claim_id")
            statuses.append(
                derive(target) if isinstance(target, str) and target in claims else "UNKNOWN"
            )
            statuses.append(str(dependency.get("interface_compatibility", "UNKNOWN")))
            statuses.append(str(dependency.get("environment_compatibility", "UNKNOWN")))
            for group_id in _strings(dependency.get("correlated_failure_group_ids")):
                group = groups.get(group_id)
                statuses.append(str(group.get("status", "UNKNOWN")) if group else "UNKNOWN")
        visiting.remove(claim_id)
        derived[claim_id] = aggregate_status(statuses)
        return derived[claim_id]

    for claim_id in claims:
        derive(claim_id)
    return derived


def _derive_revalidation(
    value: dict[str, Any],
    claim_ids: set[str],
) -> tuple[Status, set[str]]:
    changes = _objects(value.get("material_changes"))
    material = [change for change in changes if change.get("material") is True]
    affected = {
        claim_id for change in material for claim_id in _strings(change.get("affected_claim_ids"))
    }
    revalidation = value.get("revalidation")
    impact = value.get("evidence_impact")
    if not isinstance(revalidation, dict) or not isinstance(impact, dict):
        return "UNKNOWN", affected
    impact_status = str(impact.get("status", "UNKNOWN"))
    mode = revalidation.get("mode")
    if not material:
        return aggregate_status(
            [impact_status, str(revalidation.get("status", "UNKNOWN"))]
        ), affected
    if mode == "none":
        return aggregate_status([impact_status, "UNKNOWN"]), affected

    scope = _strings(revalidation.get("scope_claim_ids"))
    covered = _strings(revalidation.get("covered_change_ids"))
    material_ids = {
        str(change["change_id"]) for change in material if isinstance(change.get("change_id"), str)
    }
    invalidated = _strings(impact.get("invalidated_evidence_ids"))
    retained = _strings(revalidation.get("retained_evidence_ids"))
    required_new = _strings(impact.get("required_new_evidence_ids"))
    new = _strings(revalidation.get("new_evidence_ids"))
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
        return "FAIL", affected
    return ("PASS" if sufficient and impact_status == "PASS" else "UNKNOWN"), affected


def validate_assurance_value(
    value: dict[str, Any],
    *,
    target: str = "$",
    at: datetime | None = None,
) -> AssuranceValidationReport:
    """Validate an MNCS 0.3 assurance graph and lifecycle semantics."""

    report = _schema_report(value, "assurance", target)
    if not report.valid:
        return report

    claim_list = _objects(value.get("claims"))
    claims = _unique_map(claim_list, "claim_id", report, "$/claims", "MNCS-03-DUPLICATE-CLAIM")
    dependencies = _objects(value.get("dependencies"))
    _unique_map(
        dependencies,
        "dependency_id",
        report,
        "$/dependencies",
        "MNCS-03-DUPLICATE-DEPENDENCY",
    )
    groups = _unique_map(
        _objects(value.get("correlated_failure_groups")),
        "group_id",
        report,
        "$/correlated_failure_groups",
        "MNCS-03-DUPLICATE-CORRELATION",
    )
    claim_ids = set(claims)

    for index, dependency in enumerate(dependencies):
        for field_name in ("source_claim_id", "target_claim_id"):
            identity = dependency.get(field_name)
            if identity not in claims:
                report.add(
                    "MNCS-03-REFERENCE-MISSING",
                    f"dependency references unknown claim: {identity}",
                    f"$/dependencies/{index}/{field_name}",
                )
        for group_id in _strings(dependency.get("correlated_failure_group_ids")):
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

    for index, group in enumerate(groups.values()):
        members = _strings(group.get("claim_ids"))
        if not members <= claim_ids:
            report.add(
                "MNCS-03-CORRELATION-MEMBER-MISSING",
                "correlated group references an unknown claim",
                f"$/correlated_failure_groups/{index}/claim_ids",
            )

    _claim_cycles(claim_ids, dependencies, report)
    if not report.valid:
        return report

    derived = _derive_claim_statuses(claims, dependencies, groups, at)
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
            "MNCS-03-ROOT-CLAIM-MISSING",
            "root_claim_id does not resolve",
            "$/root_claim_id",
        )
        return report

    root_status = derived[str(root_claim_id)]
    root_status = aggregate_status(
        [
            root_status,
            str(value.get("contract_profile_status", "UNKNOWN")),
            _freshness_status(value.get("freshness"), at),
        ]
    )

    revalidation_status, affected = _derive_revalidation(value, claim_ids)
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
    if not affected <= _strings(impact.get("affected_claim_ids")):
        report.add(
            "MNCS-03-IMPACT-SCOPE-INCOMPLETE",
            "evidence impact omits materially affected claims",
            "$/evidence_impact/affected_claim_ids",
        )

    for index, change in enumerate(_objects(value.get("material_changes"))):
        if change.get("material") is True and change.get("old_identity") == change.get(
            "new_identity"
        ):
            report.add(
                "MNCS-03-MATERIAL-IDENTITY-UNCHANGED",
                "a material change requires a new identity",
                f"$/material_changes/{index}",
            )

    lifecycle = cast(dict[str, Any], value["lifecycle"])
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
    root_mncds = root.get("mncds")
    if mncds != root_mncds:
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


def validate_threat_value(
    value: dict[str, Any],
    *,
    target: str = "$",
) -> AssuranceValidationReport:
    """Validate a portable threat record and mitigation status."""

    report = _schema_report(value, "threat", target)
    if not report.valid:
        return report
    mitigations = _objects(value.get("mitigations"))
    computed = aggregate_status([str(item.get("status")) for item in mitigations])
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

    report = _schema_report(value, "measurement", target)
    if not report.valid:
        return report
    statuses = [_freshness_status(value.get("freshness"), at)]
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


def validate_rc_value(
    value: dict[str, Any],
    kind: RecordKind,
    *,
    target: str = "$",
    at: datetime | None = None,
) -> AssuranceValidationReport:
    """Dispatch one supported MNCS 0.3 record kind."""

    if kind == "contract":
        return validate_contract_value(value, target=target)
    if kind == "assurance":
        return validate_assurance_value(value, target=target, at=at)
    if kind == "threat":
        return validate_threat_value(value, target=target)
    return validate_measurement_value(value, target=target, at=at)


def validate_rc_file(
    path: Path,
    kind: RecordKind,
    *,
    at: datetime | None = None,
) -> AssuranceValidationReport:
    """Load one record and validate it without executing evidence."""

    try:
        value = load_json_object(path)
    except ManifestError as exc:
        report = AssuranceValidationReport(target=str(path), kind=kind)
        report.add("INVALID-JSON", str(exc), str(path))
        return report
    version = value.get("schema_version")
    if version != "0.3-rc.1":
        report = AssuranceValidationReport(
            target=str(path), kind=kind, valid=False, supported=False
        )
        report.add(
            "UNSUPPORTED-VERSION",
            f"unsupported {kind} schema version: {version!r}",
            "$/schema_version",
        )
        return report
    return validate_rc_value(value, kind, target=str(path), at=at)
