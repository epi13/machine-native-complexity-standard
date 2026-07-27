# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "machine"))

from study_metrics import (  # noqa: E402
    MAX_INVENTORY_ADJUSTED_ENERGY_RATIO,
    SELECTION_MAX_PUMP_START_RATIO,
    SELECTION_MAX_RAW_ENERGY_RATIO,
    aggregate,
    canonical_sha256,
    checkpoint_corruption_probe,
    compare_scenario,
    sha256,
    validate_experimental_records,
    write_deterministic_gzip,
)
from water_control.planner import (  # noqa: E402
    GeneratedTablePlanner,
    ReadableBaselinePlanner,
)
from water_control.scenarios import (  # noqa: E402
    combined_fault_suite,
    randomized_suite,
    scenario_suite,
    selection_suite,
    smoke_suite,
)
from water_control.simulator import run_scenario  # noqa: E402


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
        compare_scenario(
            baseline_by_id[scenario.scenario_id],
            candidate_by_id[scenario.scenario_id],
        )
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
        item
        for item in grouped[baseline_id]
        if item["scenario_id"] in selection_ids
    ]
    candidate_selection = [
        item
        for item in grouped[candidate_id]
        if item["scenario_id"] in selection_ids
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
        and candidate_aggregate["unmet_demand_l"]
        <= baseline_aggregate["unmet_demand_l"]
        and candidate_aggregate["overflow_l"]
        <= baseline_aggregate["overflow_l"]
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
            "This development run does not claim MNCS-L5 or MNCDS-D3. "
            "The evaluator-locked cross-host workflow is protected at "
            "execution time but is not an independent third-party evaluation, "
            "release binding, or operational evidence."
        ),
        "scenario_counts": {
            "selection": len(selection_suite()),
            "combined_fault": len(combined_fault_suite()),
            "randomized": len(randomized_suite()),
            "evaluated": len(scenarios),
        },
        "hard_gates": {
            "scenario_safety": "PASS" if scenario_gates_pass else "FAIL",
            "per_scenario_regression": (
                "PASS" if per_scenario_pass else "FAIL"
            ),
            "deterministic_replay": (
                "PASS" if deterministic_replay else "FAIL"
            ),
            "checkpoint_corruption_rejection": checkpoint_probe["status"],
            "experimental_schema_validation": schema_validation["status"],
        },
        "checkpoint_probe": checkpoint_probe,
        "schema_validation": schema_validation,
        "objective": {
            "status": "PASS" if objective_pass else "FAIL",
            "scope": "frozen selection scenarios only",
            "candidate_to_baseline_pump_start_ratio": round(starts_ratio, 6),
            "candidate_to_baseline_raw_energy_ratio": round(
                raw_energy_ratio, 6
            ),
            "candidate_to_baseline_inventory_adjusted_energy_ratio": round(
                normalized_energy_ratio, 6
            ),
            "required_pump_start_ratio_max": (
                SELECTION_MAX_PUMP_START_RATIO
            ),
            "required_raw_energy_ratio_max": SELECTION_MAX_RAW_ENERGY_RATIO,
            "required_inventory_adjusted_energy_ratio_max": (
                MAX_INVENTORY_ADJUSTED_ENERGY_RATIO
            ),
        },
        "selection_aggregates": {
            "baseline": baseline_aggregate,
            "candidate": candidate_aggregate,
        },
        "all_scenario_aggregates": all_aggregates,
        "per_scenario_comparisons": comparisons,
        "evidence_digests": {
            "scenario_definitions": canonical_sha256(
                [item.as_dict() for item in scenarios]
            ),
            "comparisons": canonical_sha256(comparisons),
        },
        "identities": {
            "planner_spec": sha256(ROOT / "generator" / "planner-spec.json"),
            "generated_planner": sha256(
                ROOT / "machine" / "generated_planner.py"
            ),
            "safety_kernel": sha256(
                ROOT / "src" / "water_control" / "safety.py"
            ),
            "simulator": sha256(
                ROOT / "src" / "water_control" / "simulator.py"
            ),
            "scenarios": sha256(
                ROOT / "src" / "water_control" / "scenarios.py"
            ),
            "preregistration": sha256(ROOT / "preregistration.json"),
        },
        "limitations": [
            "Development scenarios and deterministic randomized seeds are "
            "repository visible.",
            "Inventory normalization uses the declared duty-pump marginal "
            "energy per stored liter; it is not a pump-curve model.",
            "The plant model is a bounded digital twin and is not a hydraulic "
            "design model.",
            "No live PLC, SCADA, pump, valve, or field network is connected.",
            "The generated planner is a development candidate, not an accepted "
            "release artifact.",
            "Independent domain review, release authority, and operational "
            "lifecycle evidence remain open.",
        ],
    }
    if mode == "all":
        output = ROOT / "evidence" / "results"
        output.mkdir(parents=True, exist_ok=True)
        write_deterministic_gzip(
            output / "scenario-results.json.gz",
            {
                "schema_version": "0.2",
                "results": evaluated["observations"],
            },
        )
        write_deterministic_gzip(
            output / "study-summary.json.gz",
            summary,
        )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=("smoke", "all"),
        nargs="?",
        default="smoke",
    )
    args = parser.parse_args()
    summary = run(args.mode)
    print(json.dumps(summary, indent=2))
    return 0 if summary["development_result"] == "PASS" else 1
