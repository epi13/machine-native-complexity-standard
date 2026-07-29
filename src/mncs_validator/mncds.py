"""Offline validation for experimental MNCDS development records."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal, cast

from .errors import ManifestError
from .schemas import schema_errors
from .validation import load_json_object

MncdsStatus = Literal["PASS", "FAIL", "UNKNOWN"]

PROFILE_ORDER = {
    "MNCDS-D1": 1,
    "MNCDS-D2": 2,
    "MNCDS-D3": 3,
    "MNCDS-D4": 4,
}
REQUIRED_ROLES = {
    "contract_authority",
    "generator_authority",
    "evaluator_authority",
    "selection_authority",
    "release_authority",
    "independent_reviewer",
}
FORBIDDEN_GENERATOR_PERMISSIONS = {
    "modify_contract",
    "modify_baseline",
    "modify_evaluators",
    "modify_selection_policy",
    "modify_thresholds",
    "access_protected_holdout",
}


@dataclass(frozen=True)
class MncdsIssue:
    """One deterministic MNCDS validation finding."""

    code: str
    message: str
    path: str = ""


@dataclass
class MncdsValidationReport:
    """Validation and profile result for one MNCDS development record."""

    target: str
    valid: bool = True
    supported: bool = True
    computed_status: MncdsStatus = "PASS"
    profile: str | None = None
    record_id: str | None = None
    issues: list[MncdsIssue] = field(default_factory=list)
    warnings: list[MncdsIssue] = field(default_factory=list)

    @property
    def category(self) -> str:
        if not self.supported:
            return "UNSUPPORTED"
        if not self.valid:
            return "INVALID"
        return self.computed_status

    def add(self, code: str, message: str, path: str = "") -> None:
        self.valid = False
        self.computed_status = "FAIL"
        self.issues.append(MncdsIssue(code, message, path))

    def warn(self, code: str, message: str, path: str = "") -> None:
        self.warnings.append(MncdsIssue(code, message, path))

    def fail(self, code: str, message: str, path: str = "") -> None:
        self.computed_status = "FAIL"
        self.issues.append(MncdsIssue(code, message, path))

    def unknown(self, code: str, message: str, path: str = "") -> None:
        if self.valid and self.computed_status == "PASS":
            self.computed_status = "UNKNOWN"
        self.warnings.append(MncdsIssue(code, message, path))

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["category"] = self.category
        return result


def _objects(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [cast(dict[str, Any], item) for item in value if isinstance(item, dict)]


def _profile_at_least(profile: object, required: str) -> bool:
    return isinstance(profile, str) and PROFILE_ORDER.get(profile, 0) >= PROFILE_ORDER[required]


def _check_unique_ids(
    values: list[dict[str, Any]],
    key: str,
    report: MncdsValidationReport,
    path: str,
) -> set[str]:
    identifiers: set[str] = set()
    for index, value in enumerate(values):
        identifier = value.get(key)
        if not isinstance(identifier, str):
            continue
        if identifier in identifiers:
            report.add(
                "duplicate-id",
                f"duplicate {key}: {identifier}",
                f"{path}/{index}/{key}",
            )
        identifiers.add(identifier)
    return identifiers


def _check_lineage(
    candidates: list[dict[str, Any]],
    candidate_ids: set[str],
    report: MncdsValidationReport,
) -> None:
    parents: dict[str, list[str]] = {}
    for index, candidate in enumerate(candidates):
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str):
            continue
        parent_ids = [item for item in candidate.get("parent_ids", []) if isinstance(item, str)]
        parents[candidate_id] = parent_ids
        for parent_id in parent_ids:
            if parent_id not in candidate_ids:
                report.add(
                    "unknown-parent",
                    f"candidate parent is not recorded: {parent_id}",
                    f"$/candidates/{index}/parent_ids",
                )
            if parent_id == candidate_id:
                report.add(
                    "lineage-cycle",
                    "candidate cannot be its own parent",
                    f"$/candidates/{index}/parent_ids",
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(candidate_id: str) -> None:
        if candidate_id in visited:
            return
        if candidate_id in visiting:
            report.add("lineage-cycle", f"candidate lineage cycle includes {candidate_id}")
            return
        visiting.add(candidate_id)
        for parent_id in parents.get(candidate_id, []):
            if parent_id in parents:
                visit(parent_id)
        visiting.remove(candidate_id)
        visited.add(candidate_id)

    for candidate_id in sorted(parents):
        visit(candidate_id)


def _check_roles(value: dict[str, Any], report: MncdsValidationReport) -> dict[str, dict[str, Any]]:
    roles = _objects(value.get("roles"))
    role_names = [item.get("role") for item in roles if isinstance(item.get("role"), str)]
    role_name_set = {cast(str, name) for name in role_names}
    for missing in sorted(REQUIRED_ROLES.difference(role_name_set)):
        report.add("missing-role", f"required logical role is missing: {missing}", "$/roles")
    if len(role_names) != len(role_name_set):
        report.add(
            "duplicate-role",
            "each logical role must appear exactly once",
            "$/roles",
        )
    return {cast(str, item["role"]): item for item in roles if isinstance(item.get("role"), str)}


def _check_generator(value: dict[str, Any], report: MncdsValidationReport) -> None:
    generator = value.get("generator")
    if not isinstance(generator, dict):
        return
    permissions = generator.get("permissions")
    if not isinstance(permissions, dict):
        return
    for permission in sorted(FORBIDDEN_GENERATOR_PERMISSIONS):
        if permissions.get(permission) is True:
            report.add(
                "generator-authority-violation",
                f"generator has forbidden authority: {permission}",
                f"$/generator/permissions/{permission}",
            )


def _check_partitions(value: dict[str, Any], report: MncdsValidationReport) -> None:
    partitions = value.get("partitions")
    if not isinstance(partitions, dict):
        return
    identifiers = [
        partitions.get("development_id"),
        partitions.get("selection_id"),
        partitions.get("holdout_id"),
    ]
    present = [item for item in identifiers if isinstance(item, str)]
    if len(present) != len(set(present)):
        report.add(
            "partition-identity-overlap",
            "development, selection, and holdout partitions must have distinct identities",
            "$/partitions",
        )
    if partitions.get("holdout_contaminated") is True:
        report.add(
            "holdout-contaminated",
            "a contaminated holdout cannot support the claimed profile",
            "$/partitions/holdout_contaminated",
        )


def _selected_candidate(
    value: dict[str, Any],
    candidate_ids: set[str],
    report: MncdsValidationReport,
) -> dict[str, Any] | None:
    selection = value.get("selection")
    if not isinstance(selection, dict):
        return None
    selected_id = selection.get("selected_candidate_id")
    if not isinstance(selected_id, str) or selected_id not in candidate_ids:
        report.add(
            "selected-candidate-missing",
            "selected candidate is not present in the candidate ledger",
            "$/selection/selected_candidate_id",
        )
        return None
    for candidate in _objects(value.get("candidates")):
        if candidate.get("candidate_id") == selected_id:
            if candidate.get("disposition") != "selected":
                report.add(
                    "selection-disposition-mismatch",
                    "selected candidate must have disposition 'selected'",
                    "$/candidates",
                )
            return candidate
    return None


def _check_selection(
    value: dict[str, Any],
    selected: dict[str, Any] | None,
    evaluator_ids: set[str],
    report: MncdsValidationReport,
) -> None:
    selection = value.get("selection")
    charter = value.get("charter")
    if not isinstance(selection, dict) or not isinstance(charter, dict):
        return
    if selection.get("policy_id") != charter.get("selection_policy_id"):
        report.add(
            "selection-policy-mismatch",
            "selection record does not bind the charter selection policy",
            "$/selection/policy_id",
        )
    if selection.get("minimum_useful_benefit_met") is not True:
        report.add(
            "benefit-threshold-not-met",
            "selected candidate did not meet the predeclared useful-benefit threshold",
            "$/selection/minimum_useful_benefit_met",
        )
    if selected is None:
        return

    required_unknown = False
    for index, result in enumerate(_objects(selected.get("evaluator_results"))):
        evaluator_id = result.get("evaluator_id")
        if isinstance(evaluator_id, str) and evaluator_id not in evaluator_ids:
            report.add(
                "unknown-evaluator",
                f"candidate references unrecorded evaluator: {evaluator_id}",
                f"$/candidates/evaluator_results/{index}",
            )
        if result.get("required") is True and result.get("status") == "FAIL":
            report.add(
                "selected-required-fail",
                "selected candidate has a required FAIL",
                "$/selection/selected_candidate_id",
            )
        if result.get("required") is True and result.get("status") == "UNKNOWN":
            required_unknown = True

    if not required_unknown:
        return
    unknown_policy = selection.get("unknown_policy")
    if unknown_policy == "reject":
        report.add(
            "unknown-promoted",
            "selected candidate has required UNKNOWN evidence under a reject policy",
            "$/selection/unknown_policy",
        )
        return
    review = selection.get("human_review")
    if not isinstance(review, dict) or review.get("decision") != "accept_with_unknown":
        report.add(
            "unknown-review-missing",
            "human-review policy requires an explicit accept-with-UNKNOWN decision",
            "$/selection/human_review",
        )
        return
    report.unknown(
        "selected-with-unknown",
        (
            "record is structurally valid, but the selected candidate retains "
            "required UNKNOWN evidence"
        ),
        "$/selection/selected_candidate_id",
    )


def _check_d2(value: dict[str, Any], report: MncdsValidationReport) -> None:
    reproducibility = value.get("reproducibility")
    if not isinstance(reproducibility, dict):
        return
    reproduction_class = reproducibility.get("class")
    if reproduction_class == "NONE":
        report.add(
            "d2-reproducibility-missing",
            "D2 and above require reproducible or statistically characterized generation",
            "$/reproducibility/class",
        )
    if (
        reproduction_class in {"EXACT", "SEEDED"}
        and reproducibility.get("seeds_preserved") is not True
    ):
        report.add(
            "seed-record-missing",
            f"{reproduction_class} reproducibility requires preserved seeds",
            "$/reproducibility/seeds_preserved",
        )
    repetitions = reproducibility.get("measurement_repetitions")
    if not isinstance(repetitions, int) or repetitions < 2:
        report.add(
            "measurement-repetition-insufficient",
            "D2 and above require repeated measurements",
            "$/reproducibility/measurement_repetitions",
        )
    for index, evaluator in enumerate(_objects(value.get("evaluators"))):
        if evaluator.get("regression_corpus_id") is None:
            report.add(
                "evaluator-corpus-missing",
                "D2 and above require a versioned evaluator regression corpus",
                f"$/evaluators/{index}/regression_corpus_id",
            )


def _check_d3(
    value: dict[str, Any],
    roles: dict[str, dict[str, Any]],
    selected: dict[str, Any] | None,
    report: MncdsValidationReport,
) -> None:
    partitions = value.get("partitions")
    selection = value.get("selection")
    generator = value.get("generator")
    if isinstance(partitions, dict) and not isinstance(partitions.get("holdout_id"), str):
        report.add(
            "holdout-missing",
            "D3 and above require a protected holdout",
            "$/partitions",
        )
    if isinstance(selection, dict) and selection.get("rule_recorded_before_holdout") is not True:
        report.add(
            "selection-rule-post-hoc",
            "D3 and above require the selection rule before holdout evaluation",
            "$/selection/rule_recorded_before_holdout",
        )

    independent = [
        item
        for item in _objects(value.get("evaluators"))
        if item.get("independent") is True and item.get("purpose") in {"holdout", "independent"}
    ]
    if not independent:
        report.add(
            "independent-evaluator-missing",
            "D3 and above require an independent final evaluator",
            "$/evaluators",
        )
        return
    generator_authority = generator.get("authority_id") if isinstance(generator, dict) else None
    generator_executable = generator.get("executable_id") if isinstance(generator, dict) else None
    reviewer = roles.get("independent_reviewer", {})
    for evaluator in independent:
        if evaluator.get("authority_id") == generator_authority:
            report.add(
                "independence-authority-conflict",
                "independent evaluator shares generator authority",
                "$/evaluators",
            )
        if evaluator.get("executable_id") == generator_executable:
            report.add(
                "independence-executable-conflict",
                "independent evaluator shares generator executable identity",
                "$/evaluators",
            )
        if reviewer and evaluator.get("authority_id") != reviewer.get("authority_id"):
            report.add(
                "independent-role-mismatch",
                "independent evaluator authority does not match the declared reviewer role",
                "$/evaluators",
            )
    if selected is not None:
        used = {
            item.get("evaluator_id")
            for item in _objects(selected.get("evaluator_results"))
            if item.get("status") in {"PASS", "FAIL", "UNKNOWN"}
        }
        if not any(item.get("evaluator_id") in used for item in independent):
            report.add(
                "independent-evidence-missing",
                "selected candidate has no result from the independent evaluator",
                "$/candidates",
            )


def _check_d4(value: dict[str, Any], report: MncdsValidationReport) -> None:
    controls = value.get("release_controls")
    if not isinstance(controls, dict):
        report.add(
            "release-controls-missing",
            "D4 requires release controls",
            "$/release_controls",
        )
        return
    if controls.get("rollback_test_status") != "PASS":
        report.add(
            "rollback-not-tested",
            "D4 requires a passing rollback test",
            "$/release_controls/rollback_test_status",
        )
    drill = controls.get("regeneration_drill")
    if not isinstance(drill, dict) or drill.get("status") != "PASS":
        report.add(
            "regeneration-drill-failed",
            "D4 requires a passing regeneration or replacement drill",
            "$/release_controls/regeneration_drill",
        )


def _check_mncs_binding(value: dict[str, Any], report: MncdsValidationReport) -> None:
    charter = value.get("charter")
    binding = value.get("mncs_binding")
    selection = value.get("selection")
    if not isinstance(charter, dict) or charter.get("planned_mncs_level") is None:
        return
    if not isinstance(binding, dict):
        report.add(
            "mncs-binding-missing",
            "a planned MNCS claim requires an explicit final binding",
            "$/mncs_binding",
        )
        return
    expected = {
        "candidate_id": (
            selection.get("selected_candidate_id") if isinstance(selection, dict) else None
        ),
        "contract_id": charter.get("contract_id"),
        "environment_id": charter.get("environment_id"),
    }
    for key, expected_value in expected.items():
        if binding.get(key) != expected_value:
            report.add(
                "mncs-binding-mismatch",
                f"MNCS binding {key} does not match the development record",
                f"$/mncs_binding/{key}",
            )


def _validate_draft_value(
    value: dict[str, Any],
    *,
    target: str = "$",
) -> MncdsValidationReport:
    """Validate one decoded MNCDS development record."""

    report = MncdsValidationReport(target=target)
    report.profile = value.get("profile") if isinstance(value.get("profile"), str) else None
    report.record_id = value.get("record_id") if isinstance(value.get("record_id"), str) else None

    for error in schema_errors(value, "mncds-development-record"):
        report.add("schema", error)
    if not report.valid:
        return report

    roles = _check_roles(value, report)
    _check_generator(value, report)
    _check_partitions(value, report)

    evaluators = _objects(value.get("evaluators"))
    evaluator_ids = _check_unique_ids(evaluators, "evaluator_id", report, "$/evaluators")
    candidates = _objects(value.get("candidates"))
    candidate_ids = _check_unique_ids(candidates, "candidate_id", report, "$/candidates")
    _check_lineage(candidates, candidate_ids, report)
    selected = _selected_candidate(value, candidate_ids, report)
    _check_selection(value, selected, evaluator_ids, report)
    _check_mncs_binding(value, report)

    profile = value.get("profile")
    if _profile_at_least(profile, "MNCDS-D2"):
        _check_d2(value, report)
    if _profile_at_least(profile, "MNCDS-D3"):
        _check_d3(value, roles, selected, report)
    if _profile_at_least(profile, "MNCDS-D4"):
        _check_d4(value, report)

    return report


def _check_rc_authority_overlaps(
    value: dict[str, Any],
    report: MncdsValidationReport,
) -> dict[str, dict[str, Any]]:
    roles = _check_roles(value, report)
    grouped: dict[str, set[str]] = {}
    for role_name, role in roles.items():
        authority = role.get("authority_id")
        if isinstance(authority, str):
            grouped.setdefault(authority, set()).add(role_name)
    disclosures = {
        item.get("authority_id"): item
        for item in _objects(value.get("authority_overlaps"))
        if isinstance(item.get("authority_id"), str)
    }
    for authority, role_names in grouped.items():
        if len(role_names) > 1 and authority not in disclosures:
            report.fail(
                "authority-overlap-undisclosed",
                f"authority {authority} holds multiple roles without disclosure",
                "$/authority_overlaps",
            )
    return roles


def _check_rc_generator(value: dict[str, Any], report: MncdsValidationReport) -> None:
    generator = value.get("generator")
    permissions = generator.get("permissions") if isinstance(generator, dict) else None
    if not isinstance(permissions, dict):
        return
    for permission in sorted(FORBIDDEN_GENERATOR_PERMISSIONS):
        if permissions.get(permission) is True:
            report.fail(
                "generator-authority-violation",
                f"generator has forbidden authority: {permission}",
                f"$/generator/permissions/{permission}",
            )


def _check_rc_partitions(value: dict[str, Any], report: MncdsValidationReport) -> set[str]:
    partitions = value.get("partitions")
    if not isinstance(partitions, dict):
        return set()
    identities = {
        item
        for item in (
            partitions.get("development_id"),
            partitions.get("selection_id"),
            partitions.get("final_evaluation_id"),
        )
        if isinstance(item, str)
    }
    present = [
        item
        for item in (
            partitions.get("development_id"),
            partitions.get("selection_id"),
            partitions.get("final_evaluation_id"),
        )
        if isinstance(item, str)
    ]
    if len(present) != len(identities):
        report.fail(
            "partition-identity-overlap",
            "development, selection, and final partitions must be distinct",
            "$/partitions",
        )
    if partitions.get("holdout_contaminated") is True:
        report.fail(
            "holdout-contaminated",
            "a contaminated final partition cannot support the profile",
            "$/partitions/holdout_contaminated",
        )
    return identities


def _check_rc_epochs(
    value: dict[str, Any],
    report: MncdsValidationReport,
) -> set[str]:
    epochs = _objects(value.get("epochs"))
    epoch_ids = _check_unique_ids(epochs, "epoch_id", report, "$/epochs")
    parents: dict[str, str | None] = {}
    for index, epoch in enumerate(epochs):
        epoch_id = epoch.get("epoch_id")
        parent_id = epoch.get("parent_epoch_id")
        if not isinstance(epoch_id, str):
            continue
        parents[epoch_id] = parent_id if isinstance(parent_id, str) else None
        if isinstance(parent_id, str) and parent_id not in epoch_ids:
            report.fail(
                "unknown-epoch-parent",
                f"epoch parent is not recorded: {parent_id}",
                f"$/epochs/{index}/parent_epoch_id",
            )
        if parent_id == epoch_id:
            report.fail(
                "epoch-cycle",
                "an epoch cannot be its own parent",
                f"$/epochs/{index}/parent_epoch_id",
            )
    for epoch_id in parents:
        seen: set[str] = set()
        current: str | None = epoch_id
        while current is not None:
            if current in seen:
                report.fail("epoch-cycle", f"recursive epoch cycle includes {current}")
                break
            seen.add(current)
            current = parents.get(current)
    current_epoch = value.get("epoch_id")
    if current_epoch not in epoch_ids:
        report.fail(
            "current-epoch-missing",
            "record epoch_id is not present in epochs",
            "$/epoch_id",
        )
    return epoch_ids


def _check_rc_protected_evidence(
    value: dict[str, Any],
    partition_ids: set[str],
    report: MncdsValidationReport,
) -> None:
    evidence = _objects(value.get("protected_evidence"))
    _check_unique_ids(evidence, "evidence_id", report, "$/protected_evidence")
    for index, item in enumerate(evidence):
        if item.get("partition_id") not in partition_ids:
            report.fail(
                "protected-partition-missing",
                "protected evidence references an unknown partition",
                f"$/protected_evidence/{index}/partition_id",
            )
        if item.get("generator_access") is True or item.get("contaminated") is True:
            report.fail(
                "protected-evidence-contaminated",
                "generator access or contamination invalidates protected use",
                f"$/protected_evidence/{index}",
            )


def _check_rc_candidates(
    value: dict[str, Any],
    evaluator_ids: set[str],
    epoch_ids: set[str],
    partition_ids: set[str],
    report: MncdsValidationReport,
) -> tuple[set[str], dict[str, Any] | None]:
    candidates = _objects(value.get("candidates"))
    candidate_ids = _check_unique_ids(candidates, "candidate_id", report, "$/candidates")
    _check_lineage(candidates, candidate_ids, report)
    generator = value.get("generator")
    generator_id = generator.get("generator_id") if isinstance(generator, dict) else None
    for index, candidate in enumerate(candidates):
        if candidate.get("epoch_id") not in epoch_ids:
            report.fail(
                "candidate-epoch-missing",
                "candidate references an unknown epoch",
                f"$/candidates/{index}/epoch_id",
            )
        if candidate.get("generator_id") != generator_id:
            report.fail(
                "candidate-generator-mismatch",
                "candidate generator does not match the bound generator",
                f"$/candidates/{index}/generator_id",
            )
        if candidate.get("materially_evaluated") is True and candidate.get("retained") is not True:
            report.fail(
                "material-candidate-not-retained",
                "every materially evaluated candidate must be retained",
                f"$/candidates/{index}/retained",
            )
        for result_index, result in enumerate(_objects(candidate.get("evaluator_results"))):
            if result.get("evaluator_id") not in evaluator_ids:
                report.fail(
                    "unknown-evaluator",
                    "candidate result references an unknown evaluator",
                    f"$/candidates/{index}/evaluator_results/{result_index}/evaluator_id",
                )
            if result.get("partition_id") not in partition_ids:
                report.fail(
                    "unknown-partition",
                    "candidate result references an unknown partition",
                    f"$/candidates/{index}/evaluator_results/{result_index}/partition_id",
                )

    selection = value.get("selection")
    selected_id = selection.get("selected_candidate_id") if isinstance(selection, dict) else None
    selected = next(
        (candidate for candidate in candidates if candidate.get("candidate_id") == selected_id),
        None,
    )
    if selected is None:
        report.fail(
            "selected-candidate-missing",
            "selected candidate is not present in the ledger",
            "$/selection/selected_candidate_id",
        )
    elif selected.get("disposition") != "selected" or selected.get("retained") is not True:
        report.fail(
            "selection-disposition-mismatch",
            "selected candidate must be retained with disposition selected",
            "$/candidates",
        )
    return candidate_ids, selected


def _check_rc_selection(
    value: dict[str, Any],
    selected: dict[str, Any] | None,
    report: MncdsValidationReport,
) -> None:
    selection = value.get("selection")
    charter = value.get("charter")
    if not isinstance(selection, dict) or not isinstance(charter, dict):
        return
    if selection.get("policy_id") != charter.get("selection_policy_id"):
        report.fail(
            "selection-policy-mismatch",
            "selection does not bind the charter policy",
            "$/selection/policy_id",
        )
    if selection.get("minimum_useful_benefit_met") is not True:
        report.fail(
            "benefit-threshold-not-met",
            "selected candidate does not meet useful benefit",
            "$/selection/minimum_useful_benefit_met",
        )
    if selection.get("hard_gates_passed") is not True:
        report.fail(
            "hard-gate-failed",
            "selected candidate does not satisfy all hard gates",
            "$/selection/hard_gates_passed",
        )
    if selected is None:
        return
    required = [
        result
        for result in _objects(selected.get("evaluator_results"))
        if result.get("required") is True
    ]
    statuses = {result.get("status") for result in required}
    if "FAIL" in statuses:
        report.fail(
            "selected-required-fail",
            "selected candidate has a required FAIL",
            "$/selection/selected_candidate_id",
        )
    if "UNKNOWN" not in statuses:
        return
    if selection.get("unknown_policy") == "reject":
        report.fail(
            "unknown-promoted",
            "required UNKNOWN cannot pass a reject policy",
            "$/selection/unknown_policy",
        )
        return
    review = selection.get("human_review")
    if not isinstance(review, dict) or review.get("decision") != "accept_with_unknown":
        report.fail(
            "unknown-review-missing",
            "human review requires explicit accept-with-UNKNOWN",
            "$/selection/human_review",
        )
        return
    report.unknown(
        "selected-with-unknown",
        "selected candidate retains required UNKNOWN evidence",
        "$/selection/selected_candidate_id",
    )


def _check_rc_d2(value: dict[str, Any], report: MncdsValidationReport) -> None:
    environment = value.get("environment_lock")
    if isinstance(environment, dict) and environment.get("locked") is not True:
        report.fail(
            "environment-not-locked",
            "D2 and above require a locked environment",
            "$/environment_lock/locked",
        )
    reproducibility = value.get("reproducibility")
    if isinstance(reproducibility, dict):
        reproduction_class = reproducibility.get("class")
        if reproduction_class == "NONE":
            report.fail(
                "d2-reproducibility-missing",
                "D2 and above require a reproducible or characterized process",
                "$/reproducibility/class",
            )
        if (
            reproduction_class in {"EXACT", "SEEDED"}
            and reproducibility.get("seeds_preserved") is not True
        ):
            report.fail(
                "seed-record-missing",
                f"{reproduction_class} reproducibility requires preserved seeds",
                "$/reproducibility/seeds_preserved",
            )
        repetitions = reproducibility.get("measurement_repetitions")
        if not isinstance(repetitions, int) or repetitions < 2:
            report.fail(
                "measurement-repetition-insufficient",
                "D2 and above require repeated measurements",
                "$/reproducibility/measurement_repetitions",
            )
    for index, evaluator in enumerate(_objects(value.get("evaluators"))):
        if evaluator.get("regression_corpus_id") is None:
            report.fail(
                "evaluator-corpus-missing",
                "D2 and above require a versioned evaluator regression corpus",
                f"$/evaluators/{index}/regression_corpus_id",
            )
    for index, aggregate in enumerate(_objects(value.get("candidate_aggregates"))):
        start = aggregate.get("sequence_start")
        end = aggregate.get("sequence_end")
        if isinstance(start, int) and isinstance(end, int) and end < start:
            report.fail(
                "candidate-aggregate-range",
                "candidate aggregate sequence range is reversed",
                f"$/candidate_aggregates/{index}",
            )


def _check_rc_d3(
    value: dict[str, Any],
    roles: dict[str, dict[str, Any]],
    selected: dict[str, Any] | None,
    report: MncdsValidationReport,
) -> None:
    partitions = value.get("partitions")
    selection = value.get("selection")
    generator = value.get("generator")
    final_id = partitions.get("final_evaluation_id") if isinstance(partitions, dict) else None
    if not isinstance(final_id, str):
        report.fail(
            "holdout-missing",
            "D3 and above require a final-evaluation partition",
            "$/partitions/final_evaluation_id",
        )
    if (
        isinstance(selection, dict)
        and selection.get("rule_recorded_before_final_evaluation") is not True
    ):
        report.fail(
            "selection-rule-post-hoc",
            "selection rule must predate final evaluation",
            "$/selection/rule_recorded_before_final_evaluation",
        )
    independent = [
        evaluator
        for evaluator in _objects(value.get("evaluators"))
        if evaluator.get("independent") is True
        and evaluator.get("purpose") in {"holdout", "independent"}
    ]
    if not independent:
        report.fail(
            "independent-evaluator-missing",
            "D3 and above require a separated final evaluator",
            "$/evaluators",
        )
        return
    generator_authority = generator.get("authority_id") if isinstance(generator, dict) else None
    generator_executable = generator.get("executable_id") if isinstance(generator, dict) else None
    reviewer = roles.get("independent_reviewer", {})
    for evaluator in independent:
        if evaluator.get("authority_id") == generator_authority:
            report.fail(
                "independence-authority-conflict",
                "final evaluator shares generator authority",
                "$/evaluators",
            )
        if evaluator.get("executable_id") == generator_executable:
            report.fail(
                "independence-executable-conflict",
                "final evaluator shares generator executable",
                "$/evaluators",
            )
        if reviewer and evaluator.get("authority_id") != reviewer.get("authority_id"):
            report.fail(
                "independent-role-mismatch",
                "final evaluator is not bound to independent-review authority",
                "$/evaluators",
            )
    if selected is not None:
        independent_ids = {evaluator.get("evaluator_id") for evaluator in independent}
        used = [
            result
            for result in _objects(selected.get("evaluator_results"))
            if result.get("evaluator_id") in independent_ids
            and result.get("partition_id") == final_id
        ]
        if not used:
            report.fail(
                "independent-evidence-missing",
                "selected candidate lacks final independent evidence",
                "$/candidates",
            )
    protected = [
        item
        for item in _objects(value.get("protected_evidence"))
        if item.get("partition_id") == final_id
    ]
    if not protected:
        report.unknown(
            "protected-evidence-missing",
            "final evidence custody is unavailable",
            "$/protected_evidence",
        )
    else:
        statuses = [str(item.get("status", "UNKNOWN")) for item in protected]
        if "FAIL" in statuses:
            report.fail(
                "protected-evidence-failed",
                "protected evidence failed its custody or evaluation rule",
                "$/protected_evidence",
            )
        elif "UNKNOWN" in statuses:
            report.unknown(
                "protected-evidence-unknown",
                "protected evidence remains UNKNOWN",
                "$/protected_evidence",
            )


def _check_rc_binding(value: dict[str, Any], report: MncdsValidationReport) -> None:
    charter = value.get("charter")
    binding = value.get("mncs_binding")
    selection = value.get("selection")
    if not isinstance(charter, dict) or charter.get("planned_mncs_level") is None:
        return
    if not isinstance(binding, dict):
        report.fail(
            "mncs-binding-missing",
            "a planned MNCS claim requires a binding",
            "$/mncs_binding",
        )
        return
    expected = {
        "candidate_id": selection.get("selected_candidate_id")
        if isinstance(selection, dict)
        else None,
        "contract_id": charter.get("contract_id"),
        "environment_id": charter.get("environment_id"),
    }
    for key, expected_value in expected.items():
        if binding.get(key) != expected_value:
            report.fail(
                "mncs-binding-mismatch",
                f"MNCS binding {key} does not match the development record",
                f"$/mncs_binding/{key}",
            )


def _check_rc_d4(
    value: dict[str, Any],
    candidate_ids: set[str],
    report: MncdsValidationReport,
) -> None:
    controls = value.get("release_controls")
    if not isinstance(controls, dict):
        report.unknown(
            "release-controls-missing",
            "D4 release controls are unavailable",
            "$/release_controls",
        )
        return
    monitoring = controls.get("monitoring")
    rollback = controls.get("rollback")
    regeneration = controls.get("regeneration_or_replacement")
    retirement = controls.get("retirement")
    for code, record, field_name in (
        ("monitoring-not-established", monitoring, "status"),
        ("rollback-not-tested", rollback, "test_status"),
        ("regeneration-drill-failed", regeneration, "status"),
    ):
        status = record.get(field_name) if isinstance(record, dict) else "UNKNOWN"
        if status == "FAIL":
            report.fail(code, f"D4 control {code} failed", "$/release_controls")
        elif status != "PASS":
            report.unknown(code, f"D4 control {code} is UNKNOWN", "$/release_controls")
    if isinstance(regeneration, dict):
        replacement = regeneration.get("replacement_candidate_id")
        if replacement is not None and replacement not in candidate_ids:
            report.fail(
                "replacement-candidate-missing",
                "replacement candidate is not in the ledger",
                "$/release_controls/regeneration_or_replacement/replacement_candidate_id",
            )
    if isinstance(retirement, dict) and retirement.get("retired") is True:
        report.fail(
            "selected-candidate-retired",
            "a retired candidate cannot support a current D4 release",
            "$/release_controls/retirement",
        )


def _validate_rc_value(
    value: dict[str, Any],
    *,
    target: str,
) -> MncdsValidationReport:
    report = MncdsValidationReport(target=target)
    report.profile = value.get("profile") if isinstance(value.get("profile"), str) else None
    report.record_id = value.get("record_id") if isinstance(value.get("record_id"), str) else None
    for error in schema_errors(value, "mncds-development-record-0.1"):
        report.add("schema", error)
    if not report.valid:
        return report

    roles = _check_rc_authority_overlaps(value, report)
    _check_rc_generator(value, report)
    partition_ids = _check_rc_partitions(value, report)
    epoch_ids = _check_rc_epochs(value, report)
    _check_rc_protected_evidence(value, partition_ids, report)
    evaluators = _objects(value.get("evaluators"))
    evaluator_ids = _check_unique_ids(evaluators, "evaluator_id", report, "$/evaluators")
    candidate_ids, selected = _check_rc_candidates(
        value, evaluator_ids, epoch_ids, partition_ids, report
    )
    _check_rc_selection(value, selected, report)
    _check_rc_binding(value, report)

    profile = value.get("profile")
    if _profile_at_least(profile, "MNCDS-D2"):
        _check_rc_d2(value, report)
    if _profile_at_least(profile, "MNCDS-D3"):
        _check_rc_d3(value, roles, selected, report)
    if _profile_at_least(profile, "MNCDS-D4"):
        _check_rc_d4(value, candidate_ids, report)
    return report


def validate_development_value(
    value: dict[str, Any],
    *,
    target: str = "$",
) -> MncdsValidationReport:
    """Dispatch draft and release-candidate MNCDS records by exact version."""

    version = value.get("mncds_version")
    if version == "0.1-draft":
        return _validate_draft_value(value, target=target)
    if version == "0.1-rc.1":
        return _validate_rc_value(value, target=target)
    report = MncdsValidationReport(target=target, valid=False, supported=False)
    report.add(
        "unsupported-version",
        f"unsupported MNCDS version: {version!r}",
        "$/mncds_version",
    )
    return report


def validate_development_record(path: Path) -> MncdsValidationReport:
    """Load and validate an MNCDS development record without executing evidence."""

    try:
        value = load_json_object(path)
    except ManifestError as exc:
        report = MncdsValidationReport(target=str(path))
        report.add("invalid-json", str(exc), str(path))
        return report
    return validate_development_value(value, target=str(path))
