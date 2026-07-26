"""Offline manifest and evidence-bundle validation."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal, cast

from .errors import ManifestError
from .hashing import hash_path
from .models import ComparisonResult, Status, ValidationReport
from .schemas import schema_errors

LEVEL_GATES: dict[str, tuple[str, ...]] = {
    "MNCS-L1": ("behavioral_pass", "compiler_matrix_pass"),
    "MNCS-L2": (
        "behavioral_pass",
        "compiler_matrix_pass",
        "safety_pass",
        "resource_bounds_pass",
    ),
    "MNCS-L3": (
        "behavioral_pass",
        "compiler_matrix_pass",
        "safety_pass",
        "resource_bounds_pass",
        "required_invariants_pass",
    ),
    "MNCS-L4": (
        "behavioral_pass",
        "compiler_matrix_pass",
        "safety_pass",
        "resource_bounds_pass",
        "required_invariants_pass",
        "measurement_valid",
        "useful_benefit_threshold_met",
        "worst_case_regression_within_policy",
    ),
    "MNCS-L5": (
        "behavioral_pass",
        "holdout_pass",
        "compiler_matrix_pass",
        "safety_pass",
        "resource_bounds_pass",
        "required_invariants_pass",
        "measurement_valid",
        "useful_benefit_threshold_met",
        "worst_case_regression_within_policy",
        "provenance_complete",
    ),
}

REQUIRED_BUNDLE_DIRECTORIES = (
    "specification",
    "reference",
    "machine",
    "evidence",
    "provenance",
)


def load_json_object(path: Path) -> dict[str, Any]:
    """Load a JSON object and convert parser errors to a stable exception."""

    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestError(f"expected a JSON object: {path}")
    return value


def _safe_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ManifestError(f"evidence path escapes bundle: {relative}") from exc
    return candidate


def _verify_reference(
    root: Path,
    reference: dict[str, Any],
    report: ValidationReport,
    label: str,
) -> Path | None:
    relative = cast(str, reference.get("path", ""))
    try:
        path = _safe_path(root, relative)
    except ManifestError as exc:
        report.add("unsafe-path", str(exc), relative)
        return None
    if not path.exists():
        report.add("missing-evidence", f"{label} does not exist", relative)
        return None
    if not path.is_file():
        report.add("invalid-evidence-type", f"{label} is not a regular file", relative)
        return None
    actual = hash_path(path)
    report.checked_files += 1
    if actual != reference.get("sha256"):
        report.add(
            "hash-mismatch",
            f"{label} expected {reference.get('sha256')} but found {actual}",
            relative,
        )
    return path


def _status(values: Iterable[Status]) -> Status:
    statuses = tuple(values)
    if "FAIL" in statuses:
        return "FAIL"
    if "UNKNOWN" in statuses:
        return "UNKNOWN"
    return "PASS"


def compute_acceptance(manifest: dict[str, Any]) -> Status:
    """Compute the cumulative level result; UNKNOWN is never promoted."""

    policy = cast(dict[str, Status], manifest["acceptance_policy"])
    gates = LEVEL_GATES[cast(str, manifest["claimed_level"])]
    return _status(policy[name] for name in gates)


def _validate_invariants(
    root: Path,
    manifest: dict[str, Any],
    report: ValidationReport,
) -> list[Status]:
    results: list[Status] = []
    machine_hash = manifest["machine"]["sha256"]
    for index, reference in enumerate(manifest["invariants"]):
        path = _verify_reference(root, reference, report, f"invariant {index}")
        if path is None:
            continue
        try:
            result = load_json_object(path)
        except ManifestError as exc:
            report.add("invalid-json", str(exc), reference["path"])
            continue
        for error in schema_errors(result, "invariant-result"):
            report.add("schema", error, reference["path"])
        if result.get("source_hash") != machine_hash:
            report.add(
                "stale-invariant",
                "invariant source_hash does not identify the certified machine source",
                reference["path"],
            )
        status = result.get("status")
        if status in {"PASS", "FAIL", "UNKNOWN"}:
            results.append(cast(Status, status))
    return results


def _validate_evidence_index(
    root: Path,
    manifest: dict[str, Any],
    report: ValidationReport,
) -> None:
    reference = manifest["evidence_index"]
    path = _verify_reference(root, reference, report, "evidence index")
    if path is None:
        return
    try:
        index = load_json_object(path)
    except ManifestError as exc:
        report.add("invalid-json", str(exc), reference["path"])
        return
    for error in schema_errors(index, "evidence-index"):
        report.add("schema", error, reference["path"])
    identifiers: set[str] = set()
    for record in index.get("records", []):
        identifier = record.get("id")
        if identifier in identifiers:
            report.add(
                "duplicate-evidence-id", f"duplicate record ID: {identifier}", reference["path"]
            )
        if isinstance(identifier, str):
            identifiers.add(identifier)
        if isinstance(record, dict):
            _verify_reference(root, record, report, f"evidence record {identifier}")


def _validate_provenance(
    root: Path,
    manifest: dict[str, Any],
    report: ValidationReport,
) -> None:
    reference = manifest["provenance"]
    path = _verify_reference(root, reference, report, "provenance")
    if path is None:
        return
    try:
        provenance = load_json_object(path)
    except ManifestError as exc:
        report.add("invalid-json", str(exc), reference["path"])
        return
    for error in schema_errors(provenance, "provenance"):
        report.add("schema", error, reference["path"])
    if provenance.get("source_hash") != manifest["machine"]["sha256"]:
        report.add(
            "stale-provenance",
            "provenance source_hash differs from machine identity",
            reference["path"],
        )
    if manifest["claimed_level"] == "MNCS-L5" and not provenance.get("no_handwritten_changes"):
        report.add(
            "modified-after-certification", "L5 requires no handwritten changes", reference["path"]
        )


def _validate_performance(
    root: Path,
    manifest: dict[str, Any],
    report: ValidationReport,
) -> None:
    for index, reference in enumerate(manifest["performance_results"]):
        path = _verify_reference(root, reference, report, f"performance result {index}")
        if path is None:
            continue
        try:
            result = load_json_object(path)
        except ManifestError as exc:
            report.add("invalid-json", str(exc), reference["path"])
            continue
        for error in schema_errors(result, "performance-result"):
            report.add("schema", error, reference["path"])
        if result.get("performance_victory") and not result.get("measurement_valid"):
            report.add(
                "invalid-victory",
                "performance victory cannot be true when measurement validity is false",
                reference["path"],
            )


def validate_manifest(path: Path, *, verify_hashes: bool = True) -> ValidationReport:
    """Validate one manifest without executing referenced content."""

    report = ValidationReport(str(path))
    try:
        manifest = load_json_object(path)
    except ManifestError as exc:
        report.add("manifest", str(exc), str(path))
        return report
    for error in schema_errors(manifest, "manifest"):
        report.add("schema", error, str(path))
    if not report.valid:
        return report
    root = path.parent.resolve()
    report.declared_status = cast(Status, manifest["final_status"])
    report.computed_status = compute_acceptance(manifest)
    if report.declared_status != report.computed_status:
        report.add(
            "status-mismatch",
            f"declared {report.declared_status}, computed {report.computed_status}",
            str(path),
        )
    if manifest["complexity_profile"]["conformance_level"] != manifest["claimed_level"]:
        report.add("level-mismatch", "complexity profile level differs from claim", str(path))
    if verify_hashes:
        _verify_reference(root, manifest["reference"], report, "reference implementation")
        machine_path = _verify_reference(
            root, manifest["machine"], report, "machine implementation"
        )
        if machine_path is not None:
            with machine_path.open("rb") as stream:
                prefix = stream.read(2048).decode("utf-8", errors="replace")
            if "MNCS-GENERATED" not in prefix:
                report.add(
                    "generated-marker",
                    "machine file lacks MNCS-GENERATED marker",
                    manifest["machine"]["path"],
                )
        _validate_evidence_index(root, manifest, report)
        invariant_statuses = _validate_invariants(root, manifest, report)
        _validate_performance(root, manifest, report)
        _validate_provenance(root, manifest, report)
        if manifest["claimed_level"] in {"MNCS-L3", "MNCS-L4", "MNCS-L5"}:
            if not invariant_statuses:
                report.add(
                    "missing-invariants", "L3 and above require invariant results", str(path)
                )
            else:
                observed = _status(invariant_statuses)
                declared = manifest["acceptance_policy"]["required_invariants_pass"]
                if observed != declared:
                    report.add(
                        "invariant-status-mismatch",
                        f"invariant aggregate is {observed}, policy says {declared}",
                        str(path),
                    )
    return report


def validate_bundle(directory: Path) -> ValidationReport:
    """Validate canonical layout and its manifest."""

    report = ValidationReport(str(directory))
    if not directory.is_dir():
        report.add("bundle", "bundle directory does not exist", str(directory))
        return report
    for name in REQUIRED_BUNDLE_DIRECTORIES:
        if not (directory / name).is_dir():
            report.add("bundle-layout", f"missing directory: {name}", name)
    if not (directory / "README.md").is_file():
        report.add("bundle-layout", "missing README.md", "README.md")
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        report.add("bundle-layout", "missing manifest.json", "manifest.json")
        return report
    manifest_report = validate_manifest(manifest_path)
    report.valid = report.valid and manifest_report.valid
    report.issues.extend(manifest_report.issues)
    report.checked_files += manifest_report.checked_files
    report.declared_status = manifest_report.declared_status
    report.computed_status = manifest_report.computed_status
    return report


HIGHER_BETTER = {"throughput", "portability", "conformance_level"}
LOWER_BETTER = {
    "latency",
    "worst_case_performance",
    "memory_bytes",
    "binary_size_bytes",
    "source_size_bytes",
    "changed_lines",
    "cfg_nodes",
    "cyclomatic_complexity",
    "state_count",
    "branch_count",
    "generation_cost_seconds",
    "validation_cost_seconds",
    "unresolved_unknown_results",
}
LEVEL_VALUE = {"MNCS-L1": 1, "MNCS-L2": 2, "MNCS-L3": 3, "MNCS-L4": 4, "MNCS-L5": 5}


def compare_manifests(first: dict[str, Any], second: dict[str, Any]) -> ComparisonResult:
    """Compare candidates using explicit Pareto dimensions and no hidden weights."""

    if first["component"]["contract_id"] != second["component"]["contract_id"]:
        return ComparisonResult(
            "DIFFERENT_CONTRACT",
            "Candidates do not claim the same functional contract.",
            {},
        )
    a = first["complexity_profile"]
    b = second["complexity_profile"]
    dimensions: dict[str, str] = {}
    a_better = False
    b_better = False
    for name in sorted(HIGHER_BETTER | LOWER_BETTER):
        av = LEVEL_VALUE[a[name]] if name == "conformance_level" else a[name]
        bv = LEVEL_VALUE[b[name]] if name == "conformance_level" else b[name]
        if av == bv:
            dimensions[name] = "equal"
        elif (name in HIGHER_BETTER and av > bv) or (name in LOWER_BETTER and av < bv):
            dimensions[name] = "A better"
            a_better = True
        else:
            dimensions[name] = "B better"
            b_better = True
    if a_better and not b_better:
        relation: Literal["A_DOMINATES_B", "B_DOMINATES_A", "EQUIVALENT", "INCOMPARABLE"] = (
            "A_DOMINATES_B"
        )
        explanation = "A is no worse on every declared dimension and better on at least one."
    elif b_better and not a_better:
        relation = "B_DOMINATES_A"
        explanation = "B is no worse on every declared dimension and better on at least one."
    elif not a_better and not b_better:
        relation = "EQUIVALENT"
        explanation = "The declared Pareto dimensions are equal."
    else:
        relation = "INCOMPARABLE"
        explanation = (
            "Each candidate is better on at least one dimension; MNCS invents no hidden weights."
        )
    return ComparisonResult(relation, explanation, dimensions)
