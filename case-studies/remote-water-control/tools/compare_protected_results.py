#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def canonical_sha256(payload: object) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(args.input.glob("*.json"))
    if len(paths) != 2:
        raise SystemExit(f"expected two protected host results, found {len(paths)}")
    results = [json.loads(path.read_text()) for path in paths]
    architectures = {item["environment"]["architecture"] for item in results}
    matching_fields = ("seed_commitment", "scenario_digest", "comparison_digest")
    checks = {
        "both_hosts_pass": all(item["status"] == "PASS" for item in results),
        "distinct_architectures": len(architectures) == 2,
        "matching_seed_commitment": len({item["seed_commitment"] for item in results}) == 1,
        "matching_scenario_digest": len({item["scenario_digest"] for item in results}) == 1,
        "matching_comparison_digest": len({item["comparison_digest"] for item in results}) == 1,
        "matching_evaluator_lock": len(
            {item["evaluator_lock"]["lock_sha256"] for item in results}
        )
        == 1,
    }
    summary = {
        "schema_version": "0.1",
        "evaluation_id": "mncs.remote-water.cross-host-protected-at-execution.v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": {key: "PASS" if value else "FAIL" for key, value in checks.items()},
        "architectures": sorted(architectures),
        "host_results": [
            {
                "path": path.name,
                "architecture": result["environment"]["architecture"],
                "python": result["environment"]["python"],
                "status": result["status"],
            }
            for path, result in zip(paths, results, strict=True)
        ],
        "shared_evidence": {field: results[0][field] for field in matching_fields},
        "result_set_digest": canonical_sha256(results),
        "limitations": [
            "GitHub-hosted runners are separate fresh virtual machines, not evidence of specific physical host identity.",
            "Architecture diversity and evaluator locking do not establish evaluator independence or production suitability.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
