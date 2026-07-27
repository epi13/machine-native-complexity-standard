#!/usr/bin/env python3
"""Derive EdgeStream conformance labels from bound raw observations."""

from __future__ import annotations

from statistics import fmean
from typing import Any

from evidence_base import EVIDENCE, RESULTS, ROOT, digest, read_json, write_json

ALLOWED = {"PASS", "FAIL", "UNKNOWN"}
GATES = {
    "gate-behavioral": "differential.json",
    "gate-compiler-matrix": "compiler-matrix.json",
    "gate-safety": "sanitizers.json",
    "gate-resource-bounds": "checkpoint-recovery.json",
    "gate-mutation": "mutation.json",
    "gate-structural": "structural.json",
}


def status_of(value: Any) -> str:
    """Normalize one evidence status without treating absence as success."""

    return str(value) if value in ALLOWED else "UNKNOWN"


def aggregate(statuses: list[str]) -> str:
    """Apply MNCS dominance: FAIL, then UNKNOWN, then PASS."""

    if "FAIL" in statuses:
        return "FAIL"
    if "UNKNOWN" in statuses:
        return "UNKNOWN"
    return "PASS" if statuses and all(item == "PASS" for item in statuses) else "UNKNOWN"


def throughput_samples(benchmark: dict[str, Any]) -> tuple[list[float], list[float]]:
    """Recover baseline and candidate throughput observations from paired samples."""

    baseline: list[float] = []
    candidate: list[float] = []
    samples = benchmark.get("samples")
    if not isinstance(samples, list):
        return baseline, candidate
    for sample in samples:
        if not isinstance(sample, dict):
            continue
        for label, target in (("reference", baseline), ("candidate", candidate)):
            metric = sample.get(label)
            if not isinstance(metric, dict):
                continue
            try:
                target.append(
                    float(metric["bytes"]) * 1_000_000_000.0 / float(metric["elapsed_ns"])
                )
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                continue
    return baseline, candidate


def derive_performance() -> tuple[str, dict[str, str]]:
    """Derive all three L4 performance sub-gates and rewrite the result record."""

    benchmark = read_json(RESULTS / "benchmark.json")
    differential = status_of(read_json(RESULTS / "differential.json").get("status"))
    performance_path = EVIDENCE / "performance" / "performance-throughput.json"
    performance = read_json(performance_path)
    baseline, candidate = throughput_samples(benchmark)
    minimum = int(performance.get("minimum_sample_count", 7))
    semantic_passed = differential == "PASS"
    measurement = (
        "PASS"
        if len(baseline) >= minimum and len(candidate) >= minimum and semantic_passed
        else "FAIL"
    )
    threshold = float(performance.get("declared_threshold", 1.15))
    benefit = (
        "PASS"
        if baseline and candidate and fmean(candidate) / fmean(baseline) >= threshold
        else "FAIL"
    )
    regression = performance.get("worst_regression")
    if isinstance(regression, dict):
        observed = float(regression.get("observed_ratio", float("inf")))
        maximum = float(regression.get("maximum_allowed_ratio", 1.1))
        worst = "PASS" if observed <= maximum else "FAIL"
        regression["claimed_status"] = worst
    else:
        worst = "UNKNOWN"
    performance["checksums_or_semantic_identity"]["passed"] = semantic_passed
    performance["measurement_validity"]["claimed_status"] = measurement
    performance["benefit_threshold"]["claimed_status"] = benefit
    write_json(performance_path, performance)
    statuses = {
        "measurement_valid": measurement,
        "benefit_threshold": benefit,
        "worst_regression": worst,
    }
    return aggregate(list(statuses.values())), statuses


def refresh_index_and_manifest(final_status: str) -> None:
    """Rebind changed evidence and publish the derived manifest status."""

    index_path = EVIDENCE / "index.json"
    index = read_json(index_path)
    records = index.get("records")
    if not isinstance(records, list):
        raise TypeError("evidence index records must be a list")
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise TypeError("invalid evidence index record")
        record["sha256"] = digest(ROOT / record["path"])
    write_json(index_path, index)
    manifest_path = ROOT / "manifest.json"
    manifest = read_json(manifest_path)
    manifest["evidence_index"]["sha256"] = digest(index_path)
    manifest["final_status"] = final_status
    write_json(manifest_path, manifest)


def derive() -> str:
    """Derive gate, invariant, performance, manifest, and MNCDS statuses."""

    statuses: list[str] = []
    for gate_id, raw_name in GATES.items():
        raw_status = status_of(read_json(RESULTS / raw_name).get("status"))
        gate_path = EVIDENCE / "gates" / f"{gate_id}.json"
        gate = read_json(gate_path)
        gate["status"] = raw_status
        counts = gate.get("observation_counts")
        if isinstance(counts, dict):
            total = int(counts.get("total", 0))
            counts.update(
                passed=total if raw_status == "PASS" else 0,
                failed=total if raw_status == "FAIL" else 0,
                unknown=total if raw_status == "UNKNOWN" else 0,
            )
        write_json(gate_path, gate)
        statuses.append(raw_status)

    structural = statuses[-1]
    invariant_path = EVIDENCE / "invariants" / "invariant-bounded-storage.json"
    invariant = read_json(invariant_path)
    invariant["status"] = structural
    write_json(invariant_path, invariant)

    _, performance_statuses = derive_performance()
    statuses.extend(performance_statuses.values())
    final_status = aggregate(statuses)
    refresh_index_and_manifest(final_status)

    mncds_path = ROOT / "mncds" / "development-record.json"
    mncds = read_json(mncds_path)
    for candidate in mncds.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        for result in candidate.get("evaluator_results", []):
            if not isinstance(result, dict):
                continue
            gate_id = str(result.get("gate_id", ""))
            if gate_id in performance_statuses:
                result["status"] = performance_statuses[gate_id]
            elif gate_id == "behavioral":
                result["status"] = statuses[0]
            elif gate_id == "safety":
                result["status"] = statuses[2]
            elif gate_id == "resource_bounds":
                result["status"] = statuses[3]
    selection = mncds.get("selection")
    if isinstance(selection, dict):
        selection["minimum_useful_benefit_met"] = (
            performance_statuses["benefit_threshold"] == "PASS"
        )
    write_json(mncds_path, mncds)
    return final_status


def main() -> int:
    derive()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
