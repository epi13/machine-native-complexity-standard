#!/usr/bin/env python3
"""Correctness, safety, recovery, and performance evaluation for EdgeStream."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import shutil
import statistics
import subprocess
import time
from typing import Any

from study_support import (
    BUILD,
    RESULTS,
    ROOT,
    WORKLOADS,
    compile_binary,
    compiler_version,
    execute,
    filter_control,
    program,
    sha256,
    write_json,
)


def differential_tests() -> dict[str, Any]:
    reference = program("reference")
    candidate = program("candidate")
    cases: list[dict[str, Any]] = []
    status = "PASS"
    for workload in sorted(WORKLOADS.glob("*.bin")):
        baseline = execute(reference, workload, 4096, check=False)
        for chunk in (1, 3, 7, 31, 32, 257, 4096):
            ref = execute(reference, workload, chunk, check=False)
            cand = execute(candidate, workload, chunk, check=False)
            passed = (
                ref.stdout == baseline.stdout
                and cand.stdout == baseline.stdout
                and ref.returncode == cand.returncode
            )
            cases.append(
                {
                    "workload": workload.name,
                    "chunk": chunk,
                    "status": "PASS" if passed else "FAIL",
                    "reference_exit": ref.returncode,
                    "candidate_exit": cand.returncode,
                    "output_sha256": "sha256:" + hashlib.sha256(cand.stdout.encode()).hexdigest(),
                }
            )
            if not passed:
                status = "FAIL"
    result = {"status": status, "cases": cases}
    write_json(RESULTS / "differential.json", result)
    return result


def mutation_test() -> dict[str, Any]:
    source = bytearray((WORKLOADS / "edge-cases.bin").read_bytes()[:32])
    source[9] ^= 0x80
    path = BUILD / "mutated.bin"
    path.write_bytes(source)
    ref = execute(program("reference"), path, 5, check=False)
    cand = execute(program("candidate"), path, 5, check=False)
    passed = ref.stdout == cand.stdout and '"reason":"checksum"' in cand.stdout
    result = {
        "status": "PASS" if passed else "FAIL",
        "mutation": "single-bit payload corruption without checksum repair",
        "reference_exit": ref.returncode,
        "candidate_exit": cand.returncode,
    }
    write_json(RESULTS / "mutation.json", result)
    return result


def checkpoint_tests() -> dict[str, Any]:
    workload = WORKLOADS / "steady.bin"
    data = workload.read_bytes()
    split = (len(data) // 2 // 32) * 32
    first_path = BUILD / "recovery-first.bin"
    second_path = BUILD / "recovery-second.bin"
    first_path.write_bytes(data[:split])
    second_path.write_bytes(data[split:])
    cases: list[dict[str, Any]] = []
    status = "PASS"
    for name in ("reference", "candidate"):
        binary = program(name)
        full = execute(binary, workload, 37, check=False)
        checkpoint = BUILD / f"{name}.checkpoint"
        first = execute(binary, first_path, 11, ["--checkpoint-out", str(checkpoint)], check=False)
        second = execute(binary, second_path, 19, ["--checkpoint-in", str(checkpoint)], check=False)
        combined = filter_control(first.stdout) + filter_control(second.stdout)
        passed = combined == filter_control(full.stdout) and checkpoint.exists()
        case: dict[str, Any] = {
            "implementation": name,
            "status": "PASS" if passed else "FAIL",
            "checkpoint_bytes": checkpoint.stat().st_size if checkpoint.exists() else 0,
        }
        for step in range(1, 5):
            failed = execute(
                binary,
                first_path,
                23,
                ["--checkpoint-out", str(checkpoint), "--fail-checkpoint-step", str(step)],
                check=False,
            )
            recover = execute(
                binary,
                second_path,
                29,
                ["--checkpoint-in", str(checkpoint)],
                check=False,
            )
            fault_passed = failed.returncode != 0 and recover.returncode in (0, 1)
            case[f"fault_step_{step}"] = "PASS" if fault_passed else "FAIL"
            if case[f"fault_step_{step}"] != "PASS":
                passed = False
        case["status"] = "PASS" if passed else "FAIL"
        if not passed:
            status = "FAIL"
        cases.append(case)
    result = {"status": status, "cases": cases}
    write_json(RESULTS / "checkpoint-recovery.json", result)
    return result


def sanitizer_tests() -> dict[str, Any]:
    compiler = "clang" if shutil.which("clang") else "gcc" if shutil.which("gcc") else None
    if compiler is None:
        result = {"status": "UNKNOWN", "reason": "No supported compiler available"}
        write_json(RESULTS / "sanitizers.json", result)
        return result
    results: dict[str, Any] = {"compiler": compiler, "implementations": {}, "status": "PASS"}
    for name, source in (
        ("reference", ROOT / "reference" / "edgestream_reference.c"),
        ("candidate", ROOT / "machine" / "edgestream_generated.c"),
    ):
        binary = BUILD / f"{name}-sanitized"
        try:
            compile_binary(compiler, source, binary, sanitizers=True)
            completed = execute(binary, WORKLOADS / "hostile.bin", 17, ["--quiet"], check=False)
            passed = (
                completed.returncode in (0, 1)
                and "ERROR: AddressSanitizer" not in completed.stderr
                and "runtime error:" not in completed.stderr
            )
            results["implementations"][name] = {
                "status": "PASS" if passed else "FAIL",
                "exit": completed.returncode,
            }
            if not passed:
                results["status"] = "FAIL"
        except subprocess.CalledProcessError as error:
            results["implementations"][name] = {"status": "UNKNOWN", "stderr": error.stderr}
            results["status"] = "UNKNOWN"
    write_json(RESULTS / "sanitizers.json", results)
    return results


def parse_metric(stderr: str) -> dict[str, Any]:
    line = stderr.strip().splitlines()[-1]
    value = json.loads(line)
    assert isinstance(value, dict)
    return value


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def benchmark(repetitions: int = 7) -> dict[str, Any]:
    ref = program("reference")
    cand = program("candidate")
    workloads = [WORKLOADS / "steady.bin", WORKLOADS / "high-cardinality.bin"]
    samples: list[dict[str, Any]] = []
    ratios: list[float] = []
    worst_latency_ratio = 0.0
    for workload in workloads:
        ref_times: list[float] = []
        cand_times: list[float] = []
        for repetition in range(repetitions):
            if repetition % 2 == 0:
                order = (("reference", ref), ("candidate", cand))
            else:
                order = (("candidate", cand), ("reference", ref))
            record: dict[str, Any] = {"workload": workload.name, "repetition": repetition + 1}
            for label, binary in order:
                completed = execute(binary, workload, 4096, ["--quiet"], check=False)
                metric = parse_metric(completed.stderr)
                elapsed = float(metric["elapsed_ns"])
                record[label] = metric
                (ref_times if label == "reference" else cand_times).append(elapsed)
            ratio = float(record["reference"]["elapsed_ns"]) / float(
                record["candidate"]["elapsed_ns"]
            )
            record["throughput_ratio"] = ratio
            ratios.append(ratio)
            samples.append(record)
        p99_ratio = percentile(cand_times, 0.99) / percentile(ref_times, 0.99)
        worst_latency_ratio = max(worst_latency_ratio, p99_ratio)

    median_ratio = statistics.median(ratios)
    result = {
        "status": "PASS" if median_ratio >= 1.15 and worst_latency_ratio <= 1.10 else "FAIL",
        "repetitions_per_workload": repetitions,
        "median_paired_throughput_ratio": median_ratio,
        "worst_workload_p99_batch_latency_ratio": worst_latency_ratio,
        "threshold": 1.15,
        "maximum_latency_ratio": 1.10,
        "noise_policy": "No outlier deletion; paired measurements retained in execution order.",
        "samples": samples,
    }
    write_json(RESULTS / "benchmark.json", result)
    return result


def structural_checks() -> dict[str, Any]:
    candidate = (ROOT / "machine" / "edgestream_generated.c").read_text(encoding="utf-8")
    checks = {
        "generated_marker": "MNCS-GENERATED" in candidate,
        "bounded_storage": "ES_MAX_DEVICES" in candidate and "ES_MAX_BUFFER" in candidate,
        "no_dynamic_allocation_in_processor": (
            "malloc(" not in candidate
            and "calloc(" not in candidate
            and "realloc(" not in candidate
        ),
        "frame_length_checked": "frame_length != ES_MAX_FRAME_SIZE" in candidate,
        "checksum_precedes_accept": (
            candidate.find("expected != actual") < candidate.find("accept_frame(p")
        ),
        "no_benchmark_seed_branch": (
            "steady.bin" not in candidate and "high-cardinality.bin" not in candidate
        ),
        "checkpoint_integrity": "header.crc != crc32_slow" in candidate,
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    ledger = [
        {
            "checker": "edgestream-structural-checker",
            "version": "1.0",
            "invariant": name,
            "status": "PASS" if passed else "FAIL",
            "finding": "pattern satisfied" if passed else "required structural pattern absent",
            "candidate": sha256(ROOT / "machine" / "edgestream_generated.c"),
            "duration_ms": 0,
            "caused_repair": False,
            "suspected_false_positive": False,
            "suspected_false_negative": True,
        }
        for name, passed in checks.items()
    ]
    result = {
        "status": status,
        "checks": checks,
        "ledger": ledger,
        "limitations": [
            "Source-pattern checks do not prove C semantics; Joern was unavailable "
            "and is recorded separately as UNKNOWN."
        ],
    }
    write_json(RESULTS / "structural.json", result)
    return result


def environment_record() -> dict[str, Any]:
    value = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "gcc": compiler_version("gcc") if shutil.which("gcc") else None,
        "clang": compiler_version("clang") if shutil.which("clang") else None,
        "joern": None,
        "joern_status": "UNKNOWN",
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    write_json(RESULTS / "environment.json", value)
    return value


