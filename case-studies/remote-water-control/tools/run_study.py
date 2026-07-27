#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "machine"))

from water_control.checkpoint import CheckpointError, decode_checkpoint, encode_checkpoint  # noqa: E402
from water_control.model import ScenarioResult, SystemConfig  # noqa: E402
from water_control.planner import GeneratedTablePlanner, ReadableBaselinePlanner  # noqa: E402
from water_control.scenarios import (  # noqa: E402
    combined_fault_suite,
    randomized_suite,
    scenario_suite,
    selection_suite,
    smoke_suite,
)
from water_control.simulator import run_scenario  # noqa: E402

MAX_INVENTORY_ADJUSTED_ENERGY_RATIO = 1.05
MAX_PUMP_START_INCREASE = 1
MIN_TERMINAL_LEVEL_DELTA_PCT = -5.0
SELECTION_MAX_PUMP_START_RATIO = 0.75
SELECTION_MAX_RAW_ENERGY_RATIO = 1.10


def sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    interventions: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    for result in results:
        interventions.update(result["safety_interventions"])
        reasons.update(result["safety_reason_counts"])
    return {
        "scenario_count": len(results),
        "energy_kwh": round(sum(float(item["energy_kwh"]) for item in results), 6),
        "pump_starts": sum(int(item["pump_starts"]) for item in results),
        "unmet_demand_l": round(sum(float(item["unmet_demand_l"]) for item in results), 6),
        "overflow_l": round(sum(float(item["overflow_l"]) for item in results), 6),
        "safety_violations": sum(len(item["safety_violations"]) for item in results),
        "checkpoint_corruption_attempts": sum(
            int(item["checkpoint_corruption_attempts"]) for item in results
        ),
        "checkpoint_corruption_rejections": sum(
            int(item["checkpoint_corruption_rejections"]) for item in results
        ),
        "safety_interventions": dict(sorted(interventions.items())),
        "safety_reason_counts": dict(sorted(reasons.items())),
    }


def compare_scenario(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    config: SystemConfig | None = None,
) -> dict[str, Any]:
    active_config = config or SystemConfig()
    marginal_storage_energy_kwh_per_l = active_config.duty_power_kw / (
        active_config.duty_flow_lps * 3600.0
    )
    terminal_inventory_delta_l = (
        float(candidate["final_stored_volume_l"]) - float(baseline["final_stored_volume_l"])
    )
    adjusted_candidate_energy = float(candidate["energy_kwh"]) - (
        terminal_inventory_delta_l * marginal_storage_energy_kwh_per_l
    )
    baseline_energy = float(baseline["energy_kwh"])
    if baseline_energy <= 0.0:
        adjusted_ratio = 1.0 if adjusted_candidate_energy <= 0.0 else float("inf")
    else:
        adjusted_ratio = adjusted_candidate_energy / baseline_energy
    terminal_level_delta = float(candidate["final_level_pct"]) - float(
        baseline["final_level_pct"]
    )
    checks = {
        "inventory_adjusted_energy": adjusted_ratio <= MAX_INVENTORY_ADJUSTED_ENERGY_RATIO,
        "pump_start_regression": int(candidate["pump_starts"])
        <= int(baseline["pump_starts"]) + MAX_PUMP_START_INCREASE,
        "terminal_reserve": terminal_level_delta >= MIN_TERMINAL_LEVEL_DELTA_PCT,
        "unmet_demand": float(candidate["unmet_demand_l"])
        <= float(baseline["unmet_demand_l"]),
        "overflow": float(candidate["overflow_l"]) <= float(baseline["overflow_l"]),
        "candidate_safety": not candidate["safety_violations"],
        "checkpoint_corruption_rejection": int(candidate["checkpoint_corruption_rejections"])
        == int(candidate["checkpoint_corruption_attempts"]),
    }
    return {
        "scenario_id": candidate["scenario_id"],
        "scenario_group": candidate["scenario_group"],
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": {key: "PASS" if value else "FAIL" for key, value in checks.items()},
        "candidate_to_baseline_inventory_adjusted_energy_ratio": round(adjusted_ratio, 6),
        "candidate_inventory_adjusted_energy_kwh": round(adjusted_candidate_energy, 6),
        "candidate_to_baseline_raw_energy_ratio": round(
            float(candidate["energy_kwh"]) / max(0.000001, baseline_energy), 6
        ),
        "candidate_pump_start_delta": int(candidate["pump_starts"])
        - int(baseline["pump_starts"]),
        "candidate_terminal_level_delta_pct": round(terminal_level_delta, 6),
        "terminal_inventory_delta_l": round(terminal_inventory_delta_l, 6),
        "limits": {
            "inventory_adjusted_energy_ratio_max": MAX_INVENTORY_ADJUSTED_ENERGY_RATIO,
            "pump_start_increase_max": MAX_PUMP_START_INCREASE,
            "terminal_level_delta_pct_min": MIN_TERMINAL_LEVEL_DELTA_PCT,
            "unmet_demand_regression_l_max": 0.0,
            "overflow_regression_l_max": 0.0,
        },
    }


def checkpoint_corruption_probe(attempts: int = 8) -> dict[str, Any]:
    encoded = encode_checkpoint({"sequence": 14, "tail_hash": "abc"})
    marker = b'"sha256":"'
    start = encoded.find(marker) + len(marker)
    observations: list[str] = []
    for attempt in range(attempts):
        corrupted = bytearray(encoded)
        position = start + attempt % 64
        corrupted[position] = ord("0") if corrupted[position] != ord("0") else ord("1")
        try:
            decode_checkpoint(bytes(corrupted))
        except CheckpointError as exc:
            observations.append(str(exc))
        else:
            return {
                "status": "FAIL",
                "attempts": attempts,
                "rejections": len(observations),
                "observation": "corrupted checkpoint was accepted",
            }
    return {
        "status": "PASS",
        "attempts": attempts,
        "rejections": len(observations),
        "observations": sorted(set(observations)),
    }


def validate_experimental_records() -> dict[str, Any]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return {"status": "UNKNOWN", "observation": "jsonschema is not installed"}
    checks = (
        ("mncs-contract-profile.schema.json", ROOT / "contract" / "contract-profile.json"),
        ("mncs-assurance-case.schema.json", ROOT / "assurance-case.json"),
    )
    failures: list[str] = []
    for schema_name, record_path in checks:
        schema = json.loads((REPOSITORY_ROOT / "schemas" / schema_name).read_text())
        record = json.loads(record_path.read_text())
        errors = sorted(
            Draft202012Validator(schema).iter_errors(record), key=lambda item: item.path
        )
        failures.extend(f"{record_path.name}: {error.message}" for error in errors)
    return {"status": "FAIL" if failures else "PASS", "failures": failures}


def _scenario_group(scenario_id: str) -> str:
    selection_ids = {item.scenario_id for item in selection_suite()}
    combined_ids = {item.scenario_id for item in combined_fault_suite()}
    if scenario_id in selection_ids:
        return "selection"
    if scenario_id in combined_ids:
        return "combined_fault"
    return "randomized"


def evaluate_scenarios(scenarios: tuple[Any, ...]) -> dict[str, Any]:
    planners = (ReadableBaselinePlanner(), GeneratedTablePlanner())
    observations: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for planner in planners:
        planner_results = [
            run_scenario(
                planner,
                scenario,
                scenario_group=_scenario_group(scenario.scenario_id),
            ).as_dict()
            for scenario in scenarios
        ]
        grouped[planner.planner_id] = planner_results
        observations.extend(planner_results)
    baseline_id = ReadableBaselinePlanner.planner_id
    candidate_id = GeneratedTablePlanner.planner_id
    baseline_by_id = {item["scenario_id"]: item for item in grouped[baseline_id]}
    candidate_by_id = {item["scenario_id"]: item for item in grouped[candidate_id]}
    comparisons = [
        compare_scenario(baseline_by_id[scenario.scenario_id], candidate_by_id[scenario.scenario_id])
        for scenario in scenarios
    ]
    return {
        "observations": observations,
        "grouped": grouped,
        "comparisons": comparisons,
    }


def run(mode: str) -> dict[str, Any]:
    scenarios = smoke_suite() if mode == "smoke" else scenario_suite()
    evaluated = evaluate_scenarios(scenarios)
    grouped = evaluated["grouped"]
    candidate_id = GeneratedTablePlanner.planner_id
    baseline_id = ReadableBaselinePlanner.planner_id
    candidate_replay = [
        run_scenario(
            GeneratedTablePlanner(),
            scenario,
            scenario_group=_scenario_group(scenario.scenario_id),
        ).as_dict()
        for scenario in scenarios
    ]
    deterministic_replay = candidate_replay == grouped[candidate_id]
    checkpoint_probe = checkpoint_corruption_probe()
    schema_validation = validate_experimental_records()
    comparisons = evaluated["comparisons"]
    per_scenario_pass = all(item["status"] == "PASS" for item in comparisons)

    scenario_by_id = {item.scenario_id: item for item in scenarios}
    scenario_gates_pass = all(
        not result["safety_violations"]
        and result["sequence_end"] == result["steps"]
        and (
            scenario_by_id[result["scenario_id"]].restart_at_s is None
            or result["restart_performed"]
        )
        and result["checkpoint_corruption_attempts"]
        == result["checkpoint_corruption_rejections"]
        for result in grouped[candidate_id]
    )

    selection_ids = {item.scenario_id for item in selection_suite()}
    baseline_selection = [
        item for item in grouped[baseline_id] if item["scenario_id"] in selection_ids
    ]
    candidate_selection = [
        item for item in grouped[candidate_id] if item["scenario_id"] in selection_ids
    ]
    selection_comparisons = [
        item for item in comparisons if item["scenario_id"] in selection_ids
    ]
    baseline_aggregate = aggregate(baseline_selection)
    candidate_aggregate = aggregate(candidate_selection)
    starts_ratio = candidate_aggregate["pump_starts"] / max(
        1, baseline_aggregate["pump_starts"]
    )
    raw_energy_ratio = candidate_aggregate["energy_kwh"] / max(
        0.000001, baseline_aggregate["energy_kwh"]
    )
    normalized_energy_ratio = sum(
        float(item["candidate_inventory_adjusted_energy_kwh"])
        for item in selection_comparisons
    ) / max(0.000001, baseline_aggregate["energy_kwh"])
    objective_pass = mode == "smoke" or (
        starts_ratio <= SELECTION_MAX_PUMP_START_RATIO
        and raw_energy_ratio <= SELECTION_MAX_RAW_ENERGY_RATIO
        and normalized_energy_ratio <= MAX_INVENTORY_ADJUSTED_ENERGY_RATIO
        and candidate_aggregate["unmet_demand_l"] <= baseline_aggregate["unmet_demand_l"]
        and candidate_aggregate["overflow_l"] <= baseline_aggregate["overflow_l"]
    )
    hard_gates_pass = (
        scenario_gates_pass
        and deterministic_replay
        and checkpoint_probe["status"] == "PASS"
        and schema_validation["status"] == "PASS"
        and per_scenario_pass
    )
    development_pass = hard_gates_pass and objective_pass
    all_aggregates = {
        "baseline": aggregate(grouped[baseline_id]),
        "candidate": aggregate(grouped[candidate_id]),
    }
    summary = {
        "schema_version": "0.2",
        "study_id": "mncs.remote-water-control.development-epoch-2",
        "mode": mode,
        "development_result": "PASS" if development_pass else "FAIL",
        "formal_mncs_status": "UNKNOWN",
        "formal_mncds_status": "UNKNOWN",
        "disposition": "REVIEW_REQUIRED",
        "claim_note": (
            "This development run does not claim MNCS-L5 or MNCDS-D3. The evaluator-locked "
            "cross-host workflow is protected at execution time but is not an independent "
            "third-party evaluation, release binding, or operational evidence."
        ),
        "scenario_counts": {
            "selection": len(selection_suite()),
            "combined_fault": len(combined_fault_suite()),
            "randomized": len(randomized_suite()),
            "evaluated": len(scenarios),
        },
        "hard_gates": {
            "scenario_safety": "PASS" if scenario_gates_pass else "FAIL",
            "per_scenario_regression": "PASS" if per_scenario_pass else "FAIL",
            "deterministic_replay": "PASS" if deterministic_replay else "FAIL",
            "checkpoint_corruption_rejection": checkpoint_probe["status"],
            "experimental_schema_validation": schema_validation["status"],
        },
        "checkpoint_probe": checkpoint_probe,
        "schema_validation": schema_validation,
        "objective": {
            "status": "PASS" if objective_pass else "FAIL",
            "scope": "frozen selection scenarios only",
            "candidate_to_baseline_pump_start_ratio": round(starts_ratio, 6),
            "candidate_to_baseline_raw_energy_ratio": round(raw_energy_ratio, 6),
            "candidate_to_baseline_inventory_adjusted_energy_ratio": round(
                normalized_energy_ratio, 6
            ),
            "required_pump_start_ratio_max": SELECTION_MAX_PUMP_START_RATIO,
            "required_raw_energy_ratio_max": SELECTION_MAX_RAW_ENERGY_RATIO,
            "required_inventory_adjusted_energy_ratio_max": MAX_INVENTORY_ADJUSTED_ENERGY_RATIO,
        },
        "selection_aggregates": {
            "baseline": baseline_aggregate,
            "candidate": candidate_aggregate,
        },
        "all_scenario_aggregates": all_aggregates,
        "per_scenario_comparisons": comparisons,
        "evidence_digests": {
            "scenario_definitions": canonical_sha256([item.as_dict() for item in scenarios]),
            "comparisons": canonical_sha256(comparisons),
        },
        "identities": {
            "planner_spec": sha256(ROOT / "generator" / "planner-spec.json"),
            "generated_planner": sha256(ROOT / "machine" / "generated_planner.py"),
            "safety_kernel": sha256(ROOT / "src" / "water_control" / "safety.py"),
            "simulator": sha256(ROOT / "src" / "water_control" / "simulator.py"),
            "scenarios": sha256(ROOT / "src" / "water_control" / "scenarios.py"),
            "preregistration": sha256(ROOT / "preregistration.json"),
        },
        "limitations": [
            "Development scenarios and deterministic randomized seeds are repository visible.",
            "Inventory normalization uses the declared duty-pump marginal energy per stored liter; it is not a pump-curve model.",
            "The plant model is a bounded digital twin and is not a hydraulic design model.",
            "No live PLC, SCADA, pump, valve, or field network is connected.",
            "The generated planner is a development candidate, not an accepted release artifact.",
            "Independent domain review, release authority, and operational lifecycle evidence remain open.",
        ],
    }
    if mode == "all":
        output = ROOT / "evidence" / "results"
        output.mkdir(parents=True, exist_ok=True)
        (output / "scenario-results.json").write_text(
            json.dumps({"schema_version": "0.2", "results": evaluated["observations"]}, indent=2)
            + "\n"
        )
        (output / "study-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("smoke", "all"), nargs="?", default="smoke")
    args = parser.parse_args()
    summary = run(args.mode)
    print(json.dumps(summary, indent=2))
    return 0 if summary["development_result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
