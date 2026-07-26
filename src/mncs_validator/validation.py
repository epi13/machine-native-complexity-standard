"""Offline manifest and evidence-bundle validation."""

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import math
import os
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path, PurePosixPath
from statistics import fmean
from typing import Any, Literal, cast

from .errors import ManifestError
from .hashing import (
    DEFAULT_MAX_FILE_BYTES,
    read_regular_file,
    sha256_bytes,
    sha256_regular_file,
)
from .models import ComparisonResult, GateDecision, Status, ValidationReport
from .schemas import schema_errors

LEGACY_LEVEL_GATES: dict[str, tuple[str, ...]] = {
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

CORE_GATES = {
    "behavioral",
    "holdout",
    "safety",
    "compiler_matrix",
    "resource_bounds",
    "mutation",
    "structural",
    "measurement_valid",
    "benefit_threshold",
    "worst_regression",
    "reproducibility",
    "regeneration",
    "provenance",
    "post_certification_identity",
}
PERFORMANCE_GATES = {"measurement_valid", "benefit_threshold", "worst_regression"}
REQUIRED_BUNDLE_DIRECTORIES = (
    "specification",
    "reference",
    "machine",
    "evidence",
    "provenance",
)
MAX_INDEX_RECORDS = 2_000
MAX_BUNDLE_FILES = 4_000
WARNING_BUNDLE_FILES = 1_000
JSON_MAX_BYTES = DEFAULT_MAX_FILE_BYTES
STATUS_ORDER: dict[Status, int] = {"PASS": 0, "UNKNOWN": 1, "FAIL": 2}


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON number {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key: {key}")
        value[key] = child
    return value


def load_json_object(path: Path, *, expected_sha256: str | None = None) -> dict[str, Any]:
    """Load a bounded JSON object and convert parser errors to a stable exception."""

    try:
        content = read_regular_file(path, max_bytes=JSON_MAX_BYTES)
        if expected_sha256 is not None and sha256_bytes(content) != expected_sha256:
            raise ManifestError(f"JSON object changed after index verification: {path}")
        value: Any = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except ManifestError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ManifestError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestError(f"expected a JSON object: {path}")
    return value


def _safe_path(root: Path, relative: str) -> Path:
    if not relative or "\\" in relative:
        raise ManifestError(f"invalid evidence path: {relative}")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts:
        raise ManifestError(f"evidence path escapes bundle: {relative}")
    resolved_root = root.resolve()
    candidate = resolved_root.joinpath(*pure.parts)
    current = resolved_root
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            raise ManifestError(f"symlink evidence path is forbidden: {relative}")
    try:
        candidate.resolve(strict=False).relative_to(resolved_root)
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
    try:
        actual = sha256_regular_file(path)
    except (OSError, ValueError) as exc:
        report.add("unsafe-evidence", f"{label} cannot be safely hashed: {exc}", relative)
        return None
    report.checked_files += 1
    if actual != reference.get("sha256"):
        report.add(
            "hash-mismatch",
            f"{label} expected {reference.get('sha256')} but found {actual}",
            relative,
        )
    return path


def _aggregate_status(values: Iterable[Status]) -> Status:
    statuses = tuple(values)
    if not statuses:
        return "UNKNOWN"
    return max(statuses, key=STATUS_ORDER.__getitem__)


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _check_time_order(
    value: dict[str, Any],
    start_key: str,
    complete_key: str,
    report: ValidationReport,
    path: str,
) -> None:
    started = _parse_time(value.get(start_key))
    completed = _parse_time(value.get(complete_key))
    if started is None:
        report.add("malformed-timestamp", f"{start_key} is not a valid date-time", path)
    if completed is None:
        report.add("malformed-timestamp", f"{complete_key} is not a valid date-time", path)
    if started is not None and completed is not None and completed < started:
        report.add(
            "timestamp-order",
            f"{complete_key} precedes {start_key}",
            path,
        )


def _validate_extensions(value: Any, report: ValidationReport, path: str = "$") -> None:
    protected = CORE_GATES | {
        "required_gates",
        "on_unknown",
        "conflicting_evidence",
        "final_status",
        "status",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "extensions" and isinstance(child, dict):
                for extension_key, extension_value in child.items():
                    local_name = extension_key.split(":", 1)[-1]
                    if local_name in protected:
                        report.add(
                            "extension-shadowing",
                            f"extension attempts to redefine protected meaning: {local_name}",
                            path,
                        )
                    if isinstance(extension_value, dict) and protected.intersection(
                        extension_value
                    ):
                        report.add(
                            "extension-shadowing",
                            "extension object contains protected conformance fields",
                            path,
                        )
            _validate_extensions(child, report, f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_extensions(child, report, f"{path}/{index}")


def _schema_name(base: str, schema_version: str) -> str:
    if schema_version == "0.1":
        return f"{base}-0.1"
    if schema_version == "0.1.1":
        return f"{base}-0.1.1"
    return base


def _load_indexed_json(
    root: Path,
    record: dict[str, Any],
    schema_name: str,
    report: ValidationReport,
    cache: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    identifier = record.get("id")
    if isinstance(identifier, str) and identifier in cache:
        return cache[identifier]
    try:
        path = _safe_path(root, cast(str, record.get("path", "")))
        value = load_json_object(
            path,
            expected_sha256=cast(str, record.get("sha256")),
        )
    except ManifestError as exc:
        report.add("invalid-json", str(exc), cast(str, record.get("path", "")))
        return None
    version = value.get("schema_version")
    resolved_schema = (
        _schema_name(schema_name, version) if isinstance(version, str) else schema_name
    )
    for error in schema_errors(value, resolved_schema):
        report.add("schema", error, cast(str, record.get("path", "")))
    _validate_extensions(value, report, cast(str, record.get("path", "")))
    if isinstance(identifier, str):
        cache[identifier] = value
    return value


def _manifest_evidence_ids(manifest: dict[str, Any]) -> set[str]:
    identifiers: set[str] = set()
    for refs in manifest.get("gate_results", {}).values():
        if isinstance(refs, list):
            identifiers.update(item for item in refs if isinstance(item, str))
    for key in ("fuzz_evidence", "invariants", "performance_results"):
        values = manifest.get(key, [])
        if isinstance(values, list):
            identifiers.update(item for item in values if isinstance(item, str))
    for key in ("provenance", "post_certification_identity_check"):
        value = manifest.get(key)
        if isinstance(value, str):
            identifiers.add(value)
    for key in ("generator", "environment"):
        value = manifest.get(key, {})
        if isinstance(value, dict) and isinstance(value.get("identity_evidence_id"), str):
            identifiers.add(value["identity_evidence_id"])
    for key in ("regeneration", "rollback"):
        value = manifest.get(key, {})
        if isinstance(value, dict) and isinstance(value.get("evidence_id"), str):
            identifiers.add(value["evidence_id"])
    return identifiers


def _content_evidence_ids(value: dict[str, Any]) -> set[str]:
    identifiers: set[str] = set()
    for key, child in value.items():
        if key.endswith("_evidence_id") or key.endswith("_identity_id"):
            if isinstance(child, str):
                identifiers.add(child)
        elif key in {
            "evidence_references",
            "generator_inputs",
            "evaluator_inputs",
        } and isinstance(child, list):
            identifiers.update(item for item in child if isinstance(item, str))
    return identifiers


def _validate_evidence_index(
    root: Path,
    manifest: dict[str, Any],
    report: ValidationReport,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    reference = cast(dict[str, Any], manifest["evidence_index"])
    path = _verify_reference(root, reference, report, "evidence index")
    if path is None:
        return {}, {}
    try:
        index = load_json_object(
            path,
            expected_sha256=cast(str, reference["sha256"]),
        )
    except ManifestError as exc:
        report.add("invalid-json", str(exc), cast(str, reference["path"]))
        return {}, {}
    schema_version = cast(str, manifest.get("schema_version", "0.2"))
    for error in schema_errors(index, _schema_name("evidence-index", schema_version)):
        report.add("schema", error, cast(str, reference["path"]))
    _validate_extensions(index, report, cast(str, reference["path"]))
    records_value = index.get("records", [])
    if not isinstance(records_value, list):
        return {}, {}
    if len(records_value) > MAX_INDEX_RECORDS:
        report.add(
            "evidence-count-limit",
            f"index has {len(records_value)} records; maximum is {MAX_INDEX_RECORDS}",
            cast(str, reference["path"]),
        )
    records: dict[str, dict[str, Any]] = {}
    path_hashes: dict[str, str] = {}
    content_cache: dict[str, dict[str, Any]] = {}
    contract_id = manifest["component"]["contract_id"]
    machine_hash = manifest["machine"]["sha256"]
    for record_value in records_value[: MAX_INDEX_RECORDS + 1]:
        if not isinstance(record_value, dict):
            continue
        record = cast(dict[str, Any], record_value)
        identifier = record.get("id")
        if not isinstance(identifier, str):
            continue
        if identifier in records:
            report.add(
                "duplicate-evidence-id",
                f"duplicate record ID: {identifier}",
                cast(str, reference["path"]),
            )
            continue
        relative = record.get("path")
        digest = record.get("sha256")
        if isinstance(relative, str) and isinstance(digest, str):
            previous = path_hashes.get(relative)
            if previous is not None and previous != digest:
                report.add(
                    "conflicting-evidence-path",
                    f"path {relative} is indexed under conflicting hashes",
                    cast(str, reference["path"]),
                )
            path_hashes[relative] = digest
        if "contract_id" in record and record["contract_id"] != contract_id:
            report.add(
                "stale-contract-binding",
                f"evidence {identifier} names another contract",
                cast(str, relative or ""),
            )
        if (
            "candidate_source_hash" in record
            and record["candidate_source_hash"] != machine_hash
            and record.get("kind") not in {"witness", "other"}
        ):
            report.add(
                "stale-candidate-binding",
                f"evidence {identifier} names another candidate",
                cast(str, relative or ""),
            )
        records[identifier] = record
        _verify_reference(root, record, report, f"evidence record {identifier}")

    direct_ids = _manifest_evidence_ids(manifest)
    for identifier in sorted(direct_ids):
        if identifier not in records:
            report.add(
                "unindexed-evidence",
                f"manifest references missing evidence ID: {identifier}",
                cast(str, reference["path"]),
            )
    for kind, manifest_key in (
        ("contract", "contract"),
        ("reference", "reference"),
        ("machine", "machine"),
    ):
        expected = manifest[manifest_key]
        matches = [
            identifier
            for identifier, record in records.items()
            if record.get("kind") == kind
            and record.get("path") == expected["path"]
            and record.get("sha256") == expected["sha256"]
        ]
        if not matches:
            report.add(
                "unindexed-core-artifact",
                f"{kind} path and hash are not authoritatively indexed",
                cast(str, reference["path"]),
            )
        direct_ids.update(matches)

    graph: dict[str, list[str]] = {"manifest": sorted(direct_ids)}
    referenced = set(direct_ids)
    frontier = list(direct_ids)
    while frontier:
        identifier = frontier.pop()
        graph_record = records.get(identifier)
        if graph_record is None or not str(graph_record.get("media_type", "")).endswith("json"):
            graph.setdefault(identifier, [])
            continue
        try:
            content_path = _safe_path(root, cast(str, graph_record["path"]))
            content = load_json_object(
                content_path,
                expected_sha256=cast(str, graph_record.get("sha256")),
            )
        except ManifestError:
            graph.setdefault(identifier, [])
            continue
        dependencies = _content_evidence_ids(content)
        graph[identifier] = sorted(dependencies)
        for dependency in dependencies:
            if dependency not in records:
                report.add(
                    "unindexed-evidence-reference",
                    f"{identifier} references missing evidence ID: {dependency}",
                    cast(str, record["path"]),
                )
            elif dependency not in referenced:
                referenced.add(dependency)
                frontier.append(dependency)
    unreferenced = sorted(set(records) - referenced)
    policy = index.get("unreferenced_evidence_policy")
    for identifier in unreferenced:
        if policy == "reject":
            report.add(
                "unreferenced-evidence",
                f"indexed evidence is unreachable from the manifest: {identifier}",
                cast(str, reference["path"]),
            )
        else:
            report.warn(
                "unreferenced-evidence",
                f"indexed evidence is unreachable from the manifest: {identifier}",
                cast(str, reference["path"]),
            )
    report.evidence_graph = graph
    if manifest["claimed_level"] == "MNCS-L5" and index.get("immutable") is not True:
        report.add("mutable-evidence-index", "L5 requires an immutable evidence index", str(path))
    return records, content_cache


def _validate_identity_binding(
    root: Path,
    records: dict[str, dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    identity_id: object,
    identity_hash: object,
    report: ValidationReport,
    owner_path: str,
    expected_kind: str | None = None,
) -> None:
    if not isinstance(identity_id, str):
        return
    record = records.get(identity_id)
    if record is None:
        return
    if record.get("kind") != "identity":
        report.add(
            "identity-kind",
            f"{identity_id} is not indexed as an identity",
            owner_path,
        )
    if identity_hash != record.get("sha256"):
        report.add(
            "identity-hash-mismatch",
            f"identity hash for {identity_id} does not match its indexed content",
            owner_path,
        )
    value = _load_indexed_json(root, record, "identity", report, cache)
    if value is None:
        return
    if value.get("identity_id") != identity_id:
        report.add(
            "identity-id-mismatch",
            f"identity record content does not name {identity_id}",
            cast(str, record.get("path", "")),
        )
    if expected_kind is not None and value.get("identity_kind") != expected_kind:
        report.add(
            "identity-kind-mismatch",
            f"{identity_id} is not a {expected_kind} identity",
            cast(str, record.get("path", "")),
        )


def _validate_gate_result(
    root: Path,
    manifest: dict[str, Any],
    gate: str,
    identifier: str,
    record: dict[str, Any],
    records: dict[str, dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    report: ValidationReport,
) -> Status | None:
    if record.get("kind") != "gate_result":
        report.add(
            "gate-evidence-kind",
            f"{identifier} is not indexed as a gate result",
            cast(str, record.get("path", "")),
        )
        return None
    value = _load_indexed_json(root, record, "gate-result", report, cache)
    if value is None:
        return None
    path = cast(str, record.get("path", ""))
    if value.get("result_id") != identifier:
        report.add("gate-result-id", f"{identifier} content has another result_id", path)
    if value.get("gate_kind") != gate:
        report.add(
            "gate-kind-mismatch",
            f"{identifier} reports {value.get('gate_kind')} but is assigned to {gate}",
            path,
        )
    contract_id = manifest["component"]["contract_id"]
    machine_hash = manifest["machine"]["sha256"]
    reference_hash = manifest["reference"]["sha256"]
    if value.get("contract_id") != contract_id:
        report.add("stale-contract-binding", "gate result names another contract", path)
    if value.get("candidate_source_hash") != machine_hash:
        report.add("stale-candidate-hash", "gate result names another candidate source", path)
    if "reference_source_hash" in value and value["reference_source_hash"] != reference_hash:
        report.add("stale-reference-hash", "gate result names another reference source", path)
    component = value.get("component_identity", {})
    if isinstance(component, dict):
        expected_component = manifest["component"]
        for key in ("name", "version", "identity_hash"):
            if component.get(key) != expected_component.get(key):
                report.add(
                    "component-identity-mismatch",
                    f"gate result component {key} differs from the manifest",
                    path,
                )
    evaluator = value.get("evaluator", {})
    if isinstance(evaluator, dict):
        _validate_identity_binding(
            root,
            records,
            cache,
            evaluator.get("identity_evidence_id"),
            evaluator.get("identity_hash"),
            report,
            path,
            "evaluator",
        )
    environment = value.get("environment", {})
    if isinstance(environment, dict):
        _validate_identity_binding(
            root,
            records,
            cache,
            environment.get("identity_evidence_id"),
            environment.get("fingerprint"),
            report,
            path,
            "environment",
        )
        if environment.get("fingerprint") != manifest["environment"]["fingerprint"]:
            report.add(
                "environment-mismatch",
                "gate result environment differs from the declared environment",
                path,
            )
    counts = value.get("observation_counts", {})
    if isinstance(counts, dict) and all(
        isinstance(counts.get(key), int) for key in ("total", "passed", "failed", "unknown")
    ):
        subtotal = counts["passed"] + counts["failed"] + counts["unknown"]
        if subtotal != counts["total"]:
            report.add(
                "observation-count-mismatch",
                "gate observation subtotals do not equal total",
                path,
            )
    for evidence_id in value.get("evidence_references", []):
        if evidence_id not in records:
            report.add(
                "unindexed-supporting-evidence",
                f"gate result references unknown evidence {evidence_id}",
                path,
            )
    _check_time_order(value, "started_at", "completed_at", report, path)
    status = value.get("status")
    return cast(Status, status) if status in STATUS_ORDER else None


def _summary(samples: list[float]) -> dict[str, float]:
    return {"mean": fmean(samples), "minimum": min(samples), "maximum": max(samples)}


def _approximately_equal(first: float, second: float) -> bool:
    return math.isclose(first, second, rel_tol=1e-12, abs_tol=1e-12)


def _derive_performance(
    root: Path,
    manifest: dict[str, Any],
    identifier: str,
    record: dict[str, Any],
    records: dict[str, dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    report: ValidationReport,
) -> dict[str, Status] | None:
    if record.get("kind") != "performance":
        report.add(
            "performance-evidence-kind",
            f"{identifier} is not indexed as performance evidence",
            cast(str, record.get("path", "")),
        )
        return None
    value = _load_indexed_json(root, record, "performance-result", report, cache)
    if value is None:
        return None
    path = cast(str, record.get("path", ""))
    if value.get("result_id") != identifier:
        report.add("performance-result-id", "performance result_id differs from index ID", path)
    if value.get("contract_id") != manifest["component"]["contract_id"]:
        report.add("stale-contract-binding", "performance result names another contract", path)
    if value.get("candidate_source_hash") != manifest["machine"]["sha256"]:
        report.add(
            "performance-candidate-mismatch",
            "performance result names another candidate source",
            path,
        )
    if value.get("reference_source_hash") != manifest["reference"]["sha256"]:
        report.add(
            "performance-reference-mismatch",
            "performance result names another reference source",
            path,
        )
    policy = manifest["acceptance_policy"]
    objective = policy["objective"]
    for record_key, policy_key in (
        ("objective_metric", "metric"),
        ("unit", "unit"),
        ("direction", "direction"),
        ("declared_threshold", "threshold"),
        ("declared_noise_policy", "noise_policy"),
        ("minimum_sample_count", "minimum_sample_count"),
    ):
        if value.get(record_key) != objective.get(policy_key):
            report.add(
                f"performance-{record_key.replace('_', '-')}-mismatch",
                f"performance {record_key} differs from the predeclared policy",
                path,
            )
    if (
        value.get("worst_regression", {}).get("maximum_allowed_ratio")
        != policy["regression_policy"]["maximum_worst_case_ratio"]
    ):
        report.add(
            "performance-regression-policy-mismatch",
            "performance worst-regression limit differs from policy",
            path,
        )
    for id_key, hash_key, kind in (
        ("evaluator_identity_id", "evaluator_identity_hash", "evaluator"),
        ("benchmark_harness_identity_id", "benchmark_harness_hash", "benchmark_harness"),
        ("environment_identity_id", "environment_fingerprint", "environment"),
        ("compiler_identity_id", "compiler_identity_hash", "compiler"),
        ("build_identity_id", "build_identity_hash", "build"),
        ("corpus_identity_id", "corpus_identity_hash", "corpus"),
    ):
        _validate_identity_binding(
            root,
            records,
            cache,
            value.get(id_key),
            value.get(hash_key),
            report,
            path,
            kind,
        )
    if value.get("environment_fingerprint") != manifest["environment"]["fingerprint"]:
        report.add(
            "performance-environment-mismatch",
            "performance result environment differs from the manifest",
            path,
        )
    raw_baseline = value.get("baseline_samples", [])
    raw_candidate = value.get("candidate_samples", [])
    if not (
        isinstance(raw_baseline, list)
        and isinstance(raw_candidate, list)
        and all(isinstance(item, (int, float)) and math.isfinite(item) for item in raw_baseline)
        and all(isinstance(item, (int, float)) and math.isfinite(item) for item in raw_candidate)
    ):
        return None
    baseline = [float(item) for item in raw_baseline]
    candidate = [float(item) for item in raw_candidate]
    if any(item < 0 for item in baseline + candidate):
        report.add("invalid-performance-sample", "performance samples cannot be negative", path)
    if value.get("baseline_sample_count") != len(baseline):
        report.add("baseline-sample-count-mismatch", "baseline sample count is inconsistent", path)
    if value.get("candidate_sample_count") != len(candidate):
        report.add(
            "candidate-sample-count-mismatch",
            "candidate sample count is inconsistent",
            path,
        )
    sample_order = value.get("sample_order", [])
    if isinstance(sample_order, list) and (
        sample_order.count("baseline") != len(baseline)
        or sample_order.count("candidate") != len(candidate)
    ):
        report.add(
            "sample-order-mismatch",
            "sample order does not account for every sample",
            path,
        )
    if baseline and candidate:
        for key, observed in (
            ("baseline_summary", _summary(baseline)),
            ("candidate_summary", _summary(candidate)),
        ):
            claimed = value.get(key, {})
            if isinstance(claimed, dict):
                for metric, expected in observed.items():
                    number = claimed.get(metric)
                    if not isinstance(number, (int, float)) or not _approximately_equal(
                        float(number), expected
                    ):
                        report.add(
                            "performance-summary-mismatch",
                            f"{key}.{metric} is inconsistent with samples",
                            path,
                        )
    minimum = objective["minimum_sample_count"]
    enough_samples = len(baseline) >= minimum and len(candidate) >= minimum
    checksum = value.get("checksums_or_semantic_identity", {})
    checksum_ok = isinstance(checksum, dict) and (
        checksum.get("required") is False or checksum.get("passed") is True
    )
    measurement: Status = "PASS" if enough_samples and checksum_ok else "FAIL"
    if not baseline or not candidate:
        measurement = "UNKNOWN"
    benefit: Status = "UNKNOWN"
    worst: Status = "UNKNOWN"
    if measurement == "PASS":
        baseline_mean = fmean(baseline)
        candidate_mean = fmean(candidate)
        threshold = float(objective["threshold"])
        direction = objective["direction"]
        if direction == "higher_is_better" and baseline_mean != 0:
            ratio = candidate_mean / baseline_mean
            benefit = "PASS" if ratio >= threshold else "FAIL"
        elif direction == "lower_is_better" and candidate_mean != 0:
            ratio = baseline_mean / candidate_mean
            benefit = "PASS" if ratio >= threshold else "FAIL"
        if direction == "higher_is_better" and min(candidate) != 0:
            observed_worst_ratio = min(baseline) / min(candidate)
        elif direction == "lower_is_better" and max(baseline) != 0:
            observed_worst_ratio = max(candidate) / max(baseline)
        else:
            observed_worst_ratio = math.inf
        worst_value = value.get("worst_regression", {})
        if isinstance(worst_value, dict):
            claimed_ratio = worst_value.get("observed_ratio")
            if not isinstance(claimed_ratio, (int, float)) or not _approximately_equal(
                float(claimed_ratio), observed_worst_ratio
            ):
                report.add(
                    "worst-regression-summary-mismatch",
                    "worst-regression ratio is inconsistent with samples",
                    path,
                )
            maximum = float(policy["regression_policy"]["maximum_worst_case_ratio"])
            worst = "PASS" if observed_worst_ratio <= maximum else "FAIL"
    derived = {
        "measurement_valid": measurement,
        "benefit_threshold": benefit,
        "worst_regression": worst,
    }
    claimed_paths = {
        "measurement_valid": ("measurement_validity", "claimed_status"),
        "benefit_threshold": ("benefit_threshold", "claimed_status"),
        "worst_regression": ("worst_regression", "claimed_status"),
    }
    for gate, (container, key) in claimed_paths.items():
        claimed = value.get(container, {})
        if isinstance(claimed, dict) and claimed.get(key) != derived[gate]:
            report.add(
                "performance-derived-status-mismatch",
                f"{gate} claimed {claimed.get(key)} but derives as {derived[gate]}",
                path,
            )
    if measurement != "PASS" and benefit == "PASS":
        report.add(
            "invalid-performance-victory",
            "benefit cannot pass without valid measurement",
            path,
        )
    _check_time_order(value, "started_at", "completed_at", report, path)
    report.comparison_context.update(
        {
            "objective": str(value.get("objective_metric", "")),
            "unit": str(value.get("unit", "")),
            "direction": str(value.get("direction", "")),
            "environment": str(value.get("environment_fingerprint", "")),
            "evaluator": str(value.get("evaluator_identity_hash", "")),
            "benchmark": str(value.get("benchmark_harness_hash", "")),
        }
    )
    return derived


def _validate_invariants_new(
    root: Path,
    manifest: dict[str, Any],
    records: dict[str, dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    report: ValidationReport,
) -> None:
    for identifier in manifest.get("invariants", []):
        record = records.get(identifier)
        if record is None:
            continue
        if record.get("kind") != "invariant":
            report.add(
                "invariant-evidence-kind",
                f"{identifier} is not indexed as an invariant",
                cast(str, record.get("path", "")),
            )
            continue
        value = _load_indexed_json(root, record, "invariant-result", report, cache)
        if value is None:
            continue
        path = cast(str, record.get("path", ""))
        if value.get("result_id") != identifier:
            report.add("invariant-result-id", "invariant result_id differs from index ID", path)
        if value.get("contract_id") != manifest["component"]["contract_id"]:
            report.add("stale-contract-binding", "invariant names another contract", path)
        if value.get("candidate_source_hash") != manifest["machine"]["sha256"]:
            report.add("stale-invariant", "invariant names another candidate source", path)
        if value.get("environment_fingerprint") != manifest["environment"]["fingerprint"]:
            report.add("invariant-environment-mismatch", "invariant environment differs", path)
        _validate_identity_binding(
            root,
            records,
            cache,
            value.get("evaluator_identity_id"),
            value.get("evaluator_identity_hash"),
            report,
            path,
            "evaluator",
        )
        _check_time_order(value, "started_at", "completed_at", report, path)
    aggregate = manifest.get("structural_aggregate")
    if isinstance(aggregate, dict):
        declared = set(aggregate.get("required_invariants", []))
        actual = set(manifest.get("invariants", []))
        if declared != actual:
            report.add(
                "structural-aggregate-mismatch",
                "structural aggregate does not cover exactly the declared invariant records",
                "manifest",
            )


def _validate_provenance_new(
    root: Path,
    manifest: dict[str, Any],
    records: dict[str, dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    report: ValidationReport,
) -> None:
    identifier = manifest.get("provenance")
    if not isinstance(identifier, str):
        return
    record = records.get(identifier)
    if record is None:
        return
    if record.get("kind") != "provenance":
        report.add("provenance-kind", "provenance ID has another evidence kind", "manifest")
        return
    value = _load_indexed_json(root, record, "provenance", report, cache)
    if value is None:
        return
    path = cast(str, record.get("path", ""))
    if value.get("provenance_id") != identifier:
        report.add("provenance-id", "provenance ID differs from index ID", path)
    if value.get("contract_id") != manifest["component"]["contract_id"]:
        report.add("stale-contract-binding", "provenance names another contract", path)
    if value.get("candidate_source_hash") != manifest["machine"]["sha256"]:
        report.add("stale-provenance", "provenance names another candidate source", path)
    for id_key, hash_key, kind in (
        ("generator_identity_id", "generator_identity_hash", "generator"),
        ("evaluator_identity_id", "evaluator_identity_hash", "evaluator"),
        ("toolchain_identity_id", "toolchain_identity_hash", "toolchain"),
        ("environment_identity_id", "environment_fingerprint", "environment"),
    ):
        _validate_identity_binding(
            root,
            records,
            cache,
            value.get(id_key),
            value.get(hash_key),
            report,
            path,
            kind,
        )
    if value.get("generator_identity_id") != manifest["generator"]["identity_evidence_id"]:
        report.add("generator-identity-mismatch", "provenance generator differs", path)
    if value.get("environment_fingerprint") != manifest["environment"]["fingerprint"]:
        report.add("provenance-environment-mismatch", "provenance environment differs", path)
    for identifier_value in value.get("generator_inputs", []) + value.get("evaluator_inputs", []):
        if identifier_value not in records:
            report.add(
                "unindexed-provenance-input",
                f"provenance input {identifier_value} is not indexed",
                path,
            )
    _check_time_order(value, "generation_started_at", "generation_completed_at", report, path)
    _check_time_order(value, "evaluation_started_at", "evaluation_completed_at", report, path)
    if manifest["claimed_level"] == "MNCS-L5":
        if value.get("handwritten_change_status") != "none":
            report.add("handwritten-change", "L5 requires no handwritten changes", path)
        if value.get("regeneration_lock_state") != "locked":
            report.add("regeneration-unlocked", "L5 requires locked regeneration", path)


def _derive_new_acceptance(
    root: Path,
    manifest: dict[str, Any],
    records: dict[str, dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    report: ValidationReport,
) -> Status:
    performance_cache: dict[str, dict[str, Status]] = {}
    required = cast(list[str], manifest["acceptance_policy"]["required_gates"])
    mappings = cast(dict[str, list[str]], manifest["gate_results"])
    for gate in required:
        identifiers = mappings.get(gate, [])
        statuses: list[Status] = []
        excluded: list[str] = []
        for identifier in identifiers:
            record = records.get(identifier)
            if record is None:
                excluded.append(identifier)
                continue
            if gate in PERFORMANCE_GATES:
                derived = performance_cache.get(identifier)
                if derived is None:
                    derived = _derive_performance(
                        root,
                        manifest,
                        identifier,
                        record,
                        records,
                        cache,
                        report,
                    )
                    if derived is not None:
                        performance_cache[identifier] = derived
                if derived is not None:
                    statuses.append(derived[gate])
            else:
                status = _validate_gate_result(
                    root,
                    manifest,
                    gate,
                    identifier,
                    record,
                    records,
                    cache,
                    report,
                )
                if status is not None:
                    statuses.append(status)
        conflicts = identifiers if len(set(statuses)) > 1 else []
        if conflicts:
            report.add(
                "conflicting-gate-evidence",
                f"{gate} has conflicting observed statuses",
                "manifest",
            )
        status = _aggregate_status(statuses)
        if not identifiers or not statuses:
            report.add(
                "missing-gate-evidence",
                f"required gate {gate} has no usable indexed evidence",
                "manifest",
            )
        report.gate_statuses[gate] = GateDecision(
            status=status,
            evidence_ids=list(identifiers),
            excluded_evidence_ids=excluded,
            conflicting_evidence_ids=list(conflicts),
            reasons=(
                ["FAIL takes precedence over UNKNOWN, which takes precedence over PASS"]
                if statuses
                else ["No usable evidence was available"]
            ),
        )
    return _aggregate_status(decision.status for decision in report.gate_statuses.values())


def _validate_new_manifest(
    path: Path,
    manifest: dict[str, Any],
    report: ValidationReport,
    *,
    verify_hashes: bool,
) -> ValidationReport:
    schema_version = cast(str, manifest.get("schema_version", "0.2"))
    for error in schema_errors(manifest, _schema_name("manifest", schema_version)):
        report.add("schema", error, str(path))
    _validate_extensions(manifest, report, str(path))
    if not report.valid:
        return report
    root = path.parent.resolve()
    report.declared_status = cast(Status, manifest["final_status"])
    if manifest["acceptance_policy"]["conformance_level"] != manifest["claimed_level"]:
        report.add(
            "level-mismatch",
            "acceptance policy level differs from the claimed level",
            str(path),
        )
    if manifest["component"]["identity_hash"] != manifest["machine"]["sha256"]:
        report.add(
            "component-identity-mismatch",
            "component identity must equal the certified machine source identity",
            str(path),
        )
    if verify_hashes:
        _verify_reference(root, manifest["contract"], report, "contract")
        _verify_reference(root, manifest["reference"], report, "reference implementation")
        machine_path = _verify_reference(
            root,
            manifest["machine"],
            report,
            "machine implementation",
        )
        if machine_path is not None:
            try:
                machine_content = read_regular_file(machine_path)
                if sha256_bytes(machine_content) != manifest["machine"]["sha256"]:
                    raise ValueError("machine changed after identity verification")
                prefix = machine_content[:2048].decode("utf-8", errors="replace")
            except (OSError, ValueError) as exc:
                report.add("machine-read", str(exc), manifest["machine"]["path"])
            else:
                if "MNCS-GENERATED" not in prefix:
                    report.add(
                        "generated-marker",
                        "machine file lacks MNCS-GENERATED marker",
                        manifest["machine"]["path"],
                    )
    records, cache = _validate_evidence_index(root, manifest, report)
    _validate_identity_binding(
        root,
        records,
        cache,
        manifest["generator"]["identity_evidence_id"],
        manifest["generator"]["identity_hash"],
        report,
        str(path),
        "generator",
    )
    _validate_identity_binding(
        root,
        records,
        cache,
        manifest["environment"]["identity_evidence_id"],
        manifest["environment"]["fingerprint"],
        report,
        str(path),
        "environment",
    )
    _validate_invariants_new(root, manifest, records, cache, report)
    _validate_provenance_new(root, manifest, records, cache, report)
    report.computed_status = _derive_new_acceptance(
        root,
        manifest,
        records,
        cache,
        report,
    )
    report.claimed_level_status = report.computed_status
    if report.declared_status != report.computed_status:
        report.add(
            "status-mismatch",
            f"declared {report.declared_status}, computed {report.computed_status}",
            str(path),
        )
    report.certification_eligible = report.valid and report.computed_status == "PASS"
    return report


def _legacy_invariant_statuses(
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
            result = load_json_object(
                path,
                expected_sha256=cast(str, reference["sha256"]),
            )
        except ManifestError as exc:
            report.add("invalid-json", str(exc), reference["path"])
            continue
        for error in schema_errors(result, "invariant-result-0.1"):
            report.add("schema", error, reference["path"])
        if result.get("source_hash") != machine_hash:
            report.add(
                "stale-invariant", "legacy invariant names another source", reference["path"]
            )
        status = result.get("status")
        if status in STATUS_ORDER:
            results.append(cast(Status, status))
    return results


def _validate_legacy_manifest(
    path: Path,
    manifest: dict[str, Any],
    report: ValidationReport,
    *,
    verify_hashes: bool,
) -> ValidationReport:
    for error in schema_errors(manifest, "manifest-0.1"):
        report.add("schema", error, str(path))
    if not report.valid:
        return report
    report.legacy_self_asserted_acceptance = True
    report.reduced_assurance = True
    report.warn(
        "legacy-self-asserted-acceptance",
        "schema 0.1 acceptance statuses are manifest assertions, not evidence-derived results",
        str(path),
    )
    root = path.parent.resolve()
    report.declared_status = cast(Status, manifest["final_status"])
    gates = LEGACY_LEVEL_GATES[cast(str, manifest["claimed_level"])]
    policy = cast(dict[str, Status], manifest["acceptance_policy"])
    report.computed_status = _aggregate_status(policy[name] for name in gates)
    report.claimed_level_status = report.computed_status
    if report.declared_status != report.computed_status:
        report.add(
            "status-mismatch",
            f"declared {report.declared_status}, computed {report.computed_status}",
            str(path),
        )
    if verify_hashes:
        _verify_reference(root, manifest["reference"], report, "reference implementation")
        _verify_reference(root, manifest["machine"], report, "machine implementation")
        index_path = _verify_reference(root, manifest["evidence_index"], report, "evidence index")
        if index_path is not None:
            try:
                index = load_json_object(
                    index_path,
                    expected_sha256=cast(str, manifest["evidence_index"]["sha256"]),
                )
            except ManifestError as exc:
                report.add("invalid-json", str(exc), manifest["evidence_index"]["path"])
            else:
                for error in schema_errors(index, "evidence-index-0.1"):
                    report.add("schema", error, manifest["evidence_index"]["path"])
                identifiers: set[str] = set()
                for record in index.get("records", []):
                    identifier = record.get("id")
                    if identifier in identifiers:
                        report.add(
                            "duplicate-evidence-id",
                            f"duplicate record ID: {identifier}",
                            manifest["evidence_index"]["path"],
                        )
                    if isinstance(identifier, str):
                        identifiers.add(identifier)
                    if isinstance(record, dict):
                        _verify_reference(root, record, report, f"evidence record {identifier}")
        invariant_statuses = _legacy_invariant_statuses(root, manifest, report)
        for reference in manifest["performance_results"]:
            perf_path = _verify_reference(root, reference, report, "performance result")
            if perf_path is not None:
                try:
                    performance = load_json_object(
                        perf_path,
                        expected_sha256=cast(str, reference["sha256"]),
                    )
                except ManifestError as exc:
                    report.add("invalid-json", str(exc), reference["path"])
                else:
                    for error in schema_errors(performance, "performance-result-0.1"):
                        report.add("schema", error, reference["path"])
                    if performance.get("performance_victory") and not performance.get(
                        "measurement_valid"
                    ):
                        report.add(
                            "invalid-victory",
                            "performance victory cannot exist without valid measurement",
                            reference["path"],
                        )
        provenance_path = _verify_reference(root, manifest["provenance"], report, "provenance")
        if provenance_path is not None:
            try:
                provenance = load_json_object(
                    provenance_path,
                    expected_sha256=cast(str, manifest["provenance"]["sha256"]),
                )
            except ManifestError as exc:
                report.add("invalid-json", str(exc), manifest["provenance"]["path"])
            else:
                for error in schema_errors(provenance, "provenance-0.1"):
                    report.add("schema", error, manifest["provenance"]["path"])
                if provenance.get("source_hash") != manifest["machine"]["sha256"]:
                    report.add(
                        "stale-provenance",
                        "provenance source differs from the machine source",
                        manifest["provenance"]["path"],
                    )
        if manifest["claimed_level"] in {"MNCS-L3", "MNCS-L4", "MNCS-L5"}:
            observed = _aggregate_status(invariant_statuses)
            declared = manifest["acceptance_policy"]["required_invariants_pass"]
            if invariant_statuses and observed != declared:
                report.add(
                    "invariant-status-mismatch",
                    f"legacy invariant aggregate is {observed}, policy says {declared}",
                    str(path),
                )
    report.certification_eligible = False
    return report


def validate_manifest(
    path: Path,
    *,
    verify_hashes: bool = True,
    allow_legacy: bool = False,
) -> ValidationReport:
    """Validate one manifest without executing referenced content."""

    report = ValidationReport(str(path))
    try:
        manifest = load_json_object(path)
    except ManifestError as exc:
        report.add("manifest", str(exc), str(path))
        return report
    schema_version = manifest.get("schema_version")
    report.schema_version = schema_version if isinstance(schema_version, str) else None
    if schema_version == "0.1":
        _validate_legacy_manifest(path, manifest, report, verify_hashes=verify_hashes)
        if allow_legacy and report.valid and report.computed_status == "PASS":
            report.legacy_override_used = True
            report.certification_eligible = True
        return report
    if schema_version in {"0.1.1", "0.2"}:
        return _validate_new_manifest(path, manifest, report, verify_hashes=verify_hashes)
    report.add(
        "unsupported-schema-version",
        f"supported schema versions are 0.1, 0.1.1, and 0.2, found {schema_version!r}",
        str(path),
    )
    return report


def validate_bundle(directory: Path, *, allow_legacy: bool = False) -> ValidationReport:
    """Validate canonical layout and its manifest."""

    report = ValidationReport(str(directory))
    if not directory.is_dir():
        report.add("bundle", "bundle directory does not exist", str(directory))
        return report
    file_count = 0
    for _root, directories, files_in_root in os.walk(directory, followlinks=False):
        file_count += len(files_in_root)
        if any((Path(_root) / name).is_symlink() for name in directories):
            report.add("symlink-directory", "bundle contains a symlinked directory", _root)
    if file_count > MAX_BUNDLE_FILES:
        report.add(
            "bundle-file-count",
            f"bundle has {file_count} files; maximum is {MAX_BUNDLE_FILES}",
            str(directory),
        )
    elif file_count > WARNING_BUNDLE_FILES:
        report.warn(
            "bundle-file-count",
            f"bundle has {file_count} files; review local resource use",
            str(directory),
        )
    for name in REQUIRED_BUNDLE_DIRECTORIES:
        if not (directory / name).is_dir():
            report.add("bundle-layout", f"missing directory: {name}", name)
    if not (directory / "README.md").is_file():
        report.add("bundle-layout", "missing README.md", "README.md")
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        report.add("bundle-layout", "missing manifest.json", "manifest.json")
        return report
    manifest_report = validate_manifest(manifest_path, allow_legacy=allow_legacy)
    report.valid = report.valid and manifest_report.valid
    report.issues.extend(manifest_report.issues)
    report.warnings.extend(manifest_report.warnings)
    report.checked_files += manifest_report.checked_files
    report.declared_status = manifest_report.declared_status
    report.computed_status = manifest_report.computed_status
    report.schema_version = manifest_report.schema_version
    report.claimed_level_status = manifest_report.claimed_level_status
    report.certification_eligible = manifest_report.certification_eligible and report.valid
    report.legacy_self_asserted_acceptance = manifest_report.legacy_self_asserted_acceptance
    report.legacy_override_used = manifest_report.legacy_override_used
    report.reduced_assurance = manifest_report.reduced_assurance
    report.gate_statuses = manifest_report.gate_statuses
    report.evidence_graph = manifest_report.evidence_graph
    report.comparison_context = manifest_report.comparison_context
    return report


def _objective(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema_version") in {"0.1.1", "0.2"}:
        return cast(dict[str, Any], manifest["acceptance_policy"]["objective"])
    return cast(dict[str, Any], manifest.get("objective", {}))


def _pareto_dimensions(
    first: dict[str, Any],
    second: dict[str, Any],
) -> tuple[dict[str, str], bool, bool]:
    first_profile = first.get("comparison_profile", {})
    second_profile = second.get("comparison_profile", {})
    dimensions: dict[str, str] = {}
    a_better = False
    b_better = False
    for family, lower_is_better in (("benefit", False), ("complexity", True)):
        first_values = first_profile.get(family, {})
        second_values = second_profile.get(family, {})
        if not isinstance(first_values, dict) or not isinstance(second_values, dict):
            continue
        for name in sorted(set(first_values) & set(second_values)):
            av = first_values[name]
            bv = second_values[name]
            key = f"{family}.{name}"
            if av == bv:
                dimensions[key] = "equal"
            elif (lower_is_better and av < bv) or (not lower_is_better and av > bv):
                dimensions[key] = "A better"
                a_better = True
            else:
                dimensions[key] = "B better"
                b_better = True
    return dimensions, a_better, b_better


def compare_manifests(
    first: dict[str, Any],
    second: dict[str, Any],
    *,
    first_report: ValidationReport | None = None,
    second_report: ValidationReport | None = None,
    allow_uncertified: bool = False,
) -> ComparisonResult:
    """Compare compatible candidates using explicit dimensions and no hidden weights."""

    if first["component"]["contract_id"] != second["component"]["contract_id"]:
        return ComparisonResult(
            "DIFFERENT_CONTRACT",
            "Candidates do not claim the same functional contract.",
            {},
        )
    if first_report is not None and second_report is not None:
        if not first_report.valid or not second_report.valid:
            return ComparisonResult(
                "INVALID_EVIDENCE",
                "At least one candidate has invalid evidence.",
                {},
            )
        certified = first_report.certification_eligible and second_report.certification_eligible
    else:
        certified = False
    warning: str | None = None
    if not certified:
        if not allow_uncertified:
            return ComparisonResult(
                "UNCERTIFIED_INPUT",
                "Comparison requires certified evidence-derived PASS inputs.",
                {},
            )
        warning = "DESCRIPTIVE ONLY: one or both candidates are uncertified."
    first_objective = _objective(first)
    second_objective = _objective(second)
    if first_objective.get("metric") != second_objective.get("metric") or first_objective.get(
        "direction"
    ) != second_objective.get("direction"):
        return ComparisonResult(
            "INCOMPATIBLE_OBJECTIVE",
            "Objective metric semantics or direction differ.",
            {},
            warning=warning,
        )
    if first_objective.get("unit") != second_objective.get("unit"):
        return ComparisonResult(
            "INCOMPATIBLE_UNITS",
            "Objective units differ.",
            {},
            warning=warning,
        )
    if first_report is not None and second_report is not None:
        first_context = first_report.comparison_context
        second_context = second_report.comparison_context
        normalization = first.get("comparison_profile", {}).get("normalization")
        if first_context.get("environment") != second_context.get("environment") and not (
            normalization
            and normalization == second.get("comparison_profile", {}).get("normalization")
        ):
            return ComparisonResult(
                "INCOMPATIBLE_ENVIRONMENT",
                "Environment fingerprints differ and no shared normalization is declared.",
                {},
                warning=warning,
            )
        if first_context.get("evaluator") != second_context.get("evaluator") or first_context.get(
            "benchmark"
        ) != second_context.get("benchmark"):
            return ComparisonResult(
                "INVALID_EVIDENCE",
                "Benchmark or evaluator identities are incompatible.",
                {},
                warning=warning,
            )
    dimensions, a_better, b_better = _pareto_dimensions(first, second)
    if a_better and not b_better:
        relation: Literal["A_DOMINATES_B", "B_DOMINATES_A", "EQUIVALENT", "INCOMPARABLE"] = (
            "A_DOMINATES_B"
        )
        explanation = "A is no worse on shared dimensions and better on at least one."
    elif b_better and not a_better:
        relation = "B_DOMINATES_A"
        explanation = "B is no worse on shared dimensions and better on at least one."
    elif not a_better and not b_better:
        relation = "EQUIVALENT"
        explanation = "The shared declared benefit and complexity dimensions are equal."
    else:
        relation = "INCOMPARABLE"
        explanation = "Each candidate is better on at least one dimension; MNCS invents no weights."
    evidence_strength = {
        "A": (
            f"evidence-derived {first['claimed_level']}"
            if first.get("schema_version") in {"0.1.1", "0.2"}
            else "legacy self-asserted"
        ),
        "B": (
            f"evidence-derived {second['claimed_level']}"
            if second.get("schema_version") in {"0.1.1", "0.2"}
            else "legacy self-asserted"
        ),
    }
    return ComparisonResult(
        relation,
        explanation,
        dimensions,
        evidence_strength=evidence_strength,
        warning=warning,
    )
