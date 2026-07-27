#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "machine"))
sys.path.insert(0, str(ROOT / "tools"))

from run_study import aggregate, canonical_sha256, compare_scenario  # noqa: E402
from water_control.planner import GeneratedTablePlanner, ReadableBaselinePlanner  # noqa: E402
from water_control.scenarios import protected_suite  # noqa: E402
from water_control.simulator import run_scenario  # noqa: E402

LOCK_PATH = ROOT / "protected-evaluator-lock.json"


def file_sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def verify_lock() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text())
    failures: list[str] = []
    for relative_path, expected in lock["files"].items():
        path = ROOT / relative_path
        observed = file_sha256(path) if path.exists() else "MISSING"
        if observed != expected:
            failures.append(f"{relative_path}: expected {expected}, observed {observed}")
    return {
        "status": "FAIL" if failures else "PASS",
        "lock_id": lock["lock_id"],
        "lock_sha256": file_sha256(LOCK_PATH),
        "failures": failures,
    }


def evaluate(seed: int) -> dict[str, Any]:
    lock = verify_lock()
    scenarios = protected_suite(seed)
    baseline = [
        run_scenario(ReadableBaselinePlanner(), scenario, scenario_group="protected").as_dict()
        for scenario in scenarios
    ]
    candidate = [
        run_scenario(GeneratedTablePlanner(), scenario, scenario_group="protected").as_dict()
        for scenario in scenarios
    ]
    replay = [
        run_scenario(GeneratedTablePlanner(), scenario, scenario_group="protected").as_dict()
        for scenario in scenarios
    ]
    comparisons = [
        compare_scenario(baseline_result, candidate_result)
        for baseline_result, candidate_result in zip(baseline, candidate, strict=True)
    ]
    status = (
        lock["status"] == "PASS"
        and replay == candidate
        and all(item["status"] == "PASS" for item in comparisons)
        and all(not item["safety_violations"] for item in candidate)
    )
    return {
        "schema_version": "0.1",
        "evaluation_id": "mncs.remote-water.protected-at-execution.v1",
        "evaluation_type": "protected-at-execution-development",
        "status": "PASS" if status else "FAIL",
        "formal_mncs_status": "UNKNOWN",
        "formal_mncds_status": "UNKNOWN",
        "independent_evaluator": False,
        "best_run_selection_forbidden": True,
        "evaluator_lock": lock,
        "seed_commitment": f"sha256:{hashlib.sha256(str(seed).encode()).hexdigest()}",
        "scenario_count": len(scenarios),
        "scenario_digest": canonical_sha256([item.as_dict() for item in scenarios]),
        "comparison_digest": canonical_sha256(comparisons),
        "deterministic_replay": "PASS" if replay == candidate else "FAIL",
        "per_scenario_status": "PASS"
        if all(item["status"] == "PASS" for item in comparisons)
        else "FAIL",
        "aggregates": {
            "baseline": aggregate(baseline),
            "candidate": aggregate(candidate),
        },
        "environment": {
            "architecture": platform.machine(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "runner_name": os.environ.get("RUNNER_NAME", "local"),
            "runner_os": os.environ.get("RUNNER_OS", platform.system()),
        },
        "limitations": [
            "The exact runtime seed is generated after the candidate and evaluator lock are committed, but the scenario generator is repository visible.",
            "The evaluator authority remains correlated with the repository owner and is not an independent third party.",
            "This is a digital-twin evaluation with no physical equipment or industrial network.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
