# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
from water_control.checkpoint import CheckpointError, decode_checkpoint, encode_checkpoint
from water_control.controller import Controller
from water_control.journal import IntentJournal
from water_control.model import (
    ControllerState,
    ControlMode,
    PlannerProposal,
    SafetyDisposition,
    SystemConfig,
    TelemetryQuality,
    TelemetrySample,
)
from water_control.planner import GeneratedTablePlanner, ReadableBaselinePlanner
from water_control.safety import SafetyKernel
from water_control.scenarios import (
    combined_fault_suite,
    randomized_suite,
    scenario_suite,
    selection_suite,
)
from water_control.simulator import run_scenario

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from run_study import compare_scenario, evaluate_scenarios  # noqa: E402


def sample(
    *,
    level: float = 50.0,
    now_s: int = 1_000,
    quality: TelemetryQuality = TelemetryQuality.GOOD,
    power: bool = True,
) -> TelemetrySample:
    return TelemetrySample(now_s, now_s, level, 3.0, power, quality)


def test_generated_planner_matches_spec() -> None:
    from generated_planner import SOURCE_SPEC_SHA256

    expected = hashlib.sha256((ROOT / "generator" / "planner-spec.json").read_bytes()).hexdigest()
    assert expected == SOURCE_SPEC_SHA256


def test_safety_stops_at_high_high() -> None:
    kernel = SafetyKernel(SystemConfig())
    proposal = PlannerProposal(True, True, "test", "test")
    result = kernel.authorize(proposal, sample(level=95.0), ControllerState(), 1_000)
    assert result.mode is ControlMode.EMERGENCY
    assert not result.duty_on
    assert not result.standby_on


def test_safety_holds_on_bad_telemetry() -> None:
    kernel = SafetyKernel(SystemConfig())
    state = ControllerState(duty_on=True, standby_on=False)
    proposal = PlannerProposal(False, True, "test", "test")
    result = kernel.authorize(proposal, sample(quality=TelemetryQuality.CONFLICT), state, 1_000)
    assert result.mode is ControlMode.DEGRADED
    assert result.duty_on
    assert not result.standby_on


def test_controller_records_safety_disposition() -> None:
    controller = Controller(ReadableBaselinePlanner())
    accepted = controller.decide(sample(level=50.0), 1_000)
    assert accepted.safety_disposition is SafetyDisposition.ACCEPTED_UNCHANGED
    held = controller.decide(sample(level=40.0, now_s=1_060, quality=TelemetryQuality.STALE), 1_060)
    assert held.safety_disposition is SafetyDisposition.HELD


def test_journal_rejects_replay() -> None:
    controller = Controller(ReadableBaselinePlanner())
    intent = controller.decide(sample(), 1_000)
    with pytest.raises(ValueError, match="advance exactly once"):
        IntentJournal(last_sequence=intent.sequence).append(intent)


def test_checkpoint_corruption_is_rejected() -> None:
    encoded = bytearray(encode_checkpoint({"state": {"sequence": 1}}))
    encoded[len(encoded) // 2] ^= 1
    with pytest.raises(CheckpointError):
        decode_checkpoint(bytes(encoded))


def test_scenario_suite_is_deterministic_and_safe() -> None:
    first = [run_scenario(GeneratedTablePlanner(), item).as_dict() for item in scenario_suite()]
    second = [run_scenario(GeneratedTablePlanner(), item).as_dict() for item in scenario_suite()]
    assert first == second
    assert all(not result["safety_violations"] for result in first)
    assert all(result["sequence_end"] == result["steps"] for result in first)


def test_checkpoint_restart_preserves_sequence_during_degraded_telemetry() -> None:
    scenario = next(
        item
        for item in combined_fault_suite()
        if item.scenario_id == "restart-during-degraded-telemetry"
    )
    result = run_scenario(GeneratedTablePlanner(), scenario)
    assert result.restart_performed
    assert result.sequence_end == result.steps
    assert result.degraded_steps > 0
    assert not result.safety_violations


def test_repeated_checkpoint_corruption_is_fully_rejected() -> None:
    scenario = next(
        item
        for item in combined_fault_suite()
        if item.scenario_id == "repeated-checkpoint-corruption"
    )
    result = run_scenario(GeneratedTablePlanner(), scenario)
    assert result.checkpoint_corruption_attempts == 5
    assert result.checkpoint_corruption_rejections == 5
    assert not result.safety_violations


def test_randomized_suite_is_seeded_and_complete() -> None:
    first = randomized_suite()
    second = randomized_suite()
    assert first == second
    assert len(first) == 16
    assert any(item.power_outages and item.stale_windows for item in first)
    assert any(item.restart_at_s is not None for item in first)


def test_demand_model_error_changes_observation_not_plant_demand() -> None:
    scenario = next(
        item for item in combined_fault_suite() if item.scenario_id == "demand-model-error"
    )
    result = run_scenario(GeneratedTablePlanner(), scenario)
    expected_actual = sum((end - start) * demand for start, end, demand in scenario.demand_profile)
    assert result.actual_demand_l == expected_actual
    assert result.demand_observation_scale == 0.75
    assert result.unmet_demand_l == 0.0


def test_every_scenario_passes_predeclared_regression_limits() -> None:
    evaluated = evaluate_scenarios(scenario_suite())
    assert all(item["status"] == "PASS" for item in evaluated["comparisons"])


def test_terminal_inventory_normalization_prevents_borrowed_benefit() -> None:
    scenario = next(item for item in selection_suite() if item.scenario_id == "peak-demand")
    baseline = run_scenario(ReadableBaselinePlanner(), scenario).as_dict()
    candidate = run_scenario(GeneratedTablePlanner(), scenario).as_dict()
    comparison = compare_scenario(baseline, candidate)
    assert comparison["candidate_terminal_level_delta_pct"] >= -5.0
    assert comparison["candidate_to_baseline_inventory_adjusted_energy_ratio"] <= 1.05


def test_candidate_meets_frozen_selection_objective() -> None:
    baseline = [run_scenario(ReadableBaselinePlanner(), item) for item in selection_suite()]
    candidate = [run_scenario(GeneratedTablePlanner(), item) for item in selection_suite()]
    baseline_starts = sum(item.pump_starts for item in baseline)
    candidate_starts = sum(item.pump_starts for item in candidate)
    baseline_energy = sum(item.energy_kwh for item in baseline)
    candidate_energy = sum(item.energy_kwh for item in candidate)
    assert candidate_starts / baseline_starts <= 0.75
    assert candidate_energy / baseline_energy <= 1.10
    assert sum(item.unmet_demand_l for item in candidate) == 0.0
    assert sum(item.overflow_l for item in candidate) == 0.0


def test_preregistration_is_epoch_2_json() -> None:
    record = json.loads((ROOT / "preregistration.json").read_text())
    assert record["study_id"] == "mncs.remote-water-control.development-epoch-2"
