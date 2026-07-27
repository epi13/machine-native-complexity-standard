#!/usr/bin/env python3
"""Build, test, benchmark, and emit EdgeStream development evidence."""

from __future__ import annotations

import argparse
import json
from typing import Any

from study_evaluation import (
    benchmark,
    checkpoint_tests,
    differential_tests,
    environment_record,
    mutation_test,
    sanitizer_tests,
    structural_checks,
)
from study_support import (
    RESULTS,
    build_all,
    generate_candidate,
    generate_workloads,
    program,
    sha256,
    write_json,
)


def summary_status(results: dict[str, dict[str, Any]]) -> str:
    statuses = [value.get("status", "UNKNOWN") for value in results.values()]
    if "FAIL" in statuses:
        return "FAIL"
    if "UNKNOWN" in statuses:
        return "UNKNOWN"
    return "PASS"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("all", "generate", "build", "test", "benchmark"),
        nargs="?",
        default="all",
    )
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)

    if args.command in ("all", "generate"):
        generate_candidate()
        generate_workloads()
    if args.command in ("all", "build"):
        build_all()
    if args.command in ("all", "test"):
        if not program("reference").exists() or not program("candidate").exists():
            build_all()
        results = {
            "generation": generate_candidate(),
            "differential": differential_tests(),
            "mutation": mutation_test(),
            "checkpoint_recovery": checkpoint_tests(),
            "sanitizers": sanitizer_tests(),
            "structural": structural_checks(),
        }
        write_json(
            RESULTS / "test-summary.json",
            {"status": summary_status(results), "results": results},
        )
    if args.command in ("all", "benchmark"):
        if not program("reference").exists() or not program("candidate").exists():
            build_all()
        benchmark_result = benchmark()
        write_json(RESULTS / "benchmark-summary.json", benchmark_result)
    if args.command == "all":
        environment_record()
        evidence_files = sorted(
            path
            for path in RESULTS.glob("*.json")
            if path.name != "study-summary.json"
        )
        statuses: dict[str, str] = {}
        for path in evidence_files:
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict) and "status" in value:
                statuses[path.stem] = str(value["status"])
        if "FAIL" in statuses.values():
            overall = "FAIL"
        elif "UNKNOWN" in statuses.values():
            overall = "UNKNOWN"
        else:
            overall = "PASS"
        write_json(
            RESULTS / "study-summary.json",
            {
                "status": overall,
                "target": "MNCDS-D2 / MNCS-L4 development study",
                "statuses": statuses,
                "evidence": {path.name: sha256(path) for path in evidence_files},
                "limitations": [
                    "Joern was unavailable, so Joern-specific structural evidence remains UNKNOWN.",
                    "The checked-in holdout is separated but not blind third-party evidence.",
                    "This development run is not an accredited certification claim.",
                ],
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
