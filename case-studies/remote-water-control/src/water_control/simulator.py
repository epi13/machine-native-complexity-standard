# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from water_control.checkpoint import CheckpointError, decode_checkpoint, encode_checkpoint
from water_control.controller import Controller
from water_control.model import (
    ControlMode,
    PlantState,
    Scenario,
    ScenarioResult,
    SystemConfig,
    TelemetryQuality,
    TelemetrySample,
)
from water_control.planner import Planner


@dataclass
class Plant:
    config: SystemConfig
    state: PlantState

    @classmethod
    def at_level(cls, config: SystemConfig, level_pct: float) -> Plant:
        return cls(config, PlantState(config.tank_capacity_l * level_pct / 100.0))

    @property
    def level_pct(self) -> float:
        return self.state.tank_volume_l / self.config.tank_capacity_l * 100.0

    def step(
        self,
        *,
        duty_command: bool,
        standby_command: bool,
        demand_lps: float,
        power_available: bool,
        duration_s: int,
    ) -> None:
        duty_running = duty_command and power_available
        standby_running = standby_command and power_available
        if duty_running and not self.state.duty_running:
            self.state.duty_starts += 1
        if standby_running and not self.state.standby_running:
            self.state.standby_starts += 1
        self.state.duty_running = duty_running
        self.state.standby_running = standby_running
        inflow_l = duration_s * (
            self.config.duty_flow_lps * int(duty_running)
            + self.config.standby_flow_lps * int(standby_running)
        )
        demand_l = duration_s * demand_lps
        available_l = self.state.tank_volume_l + inflow_l
        delivered_l = min(available_l, demand_l)
        self.state.unmet_demand_l += demand_l - delivered_l
        next_volume_l = available_l - delivered_l
        if next_volume_l > self.config.tank_capacity_l:
            self.state.overflow_l += next_volume_l - self.config.tank_capacity_l
            next_volume_l = self.config.tank_capacity_l
        self.state.tank_volume_l = max(0.0, next_volume_l)
        self.state.energy_kwh += duration_s / 3600.0 * (
            self.config.duty_power_kw * int(duty_running)
            + self.config.standby_power_kw * int(standby_running)
        )


def _inside(now_s: int, windows: tuple[tuple[int, int], ...]) -> bool:
    return any(start <= now_s < end for start, end in windows)


def _demand_at(now_s: int, scenario: Scenario) -> float:
    for start, end, demand in scenario.demand_profile:
        if start <= now_s < end:
            return demand
    raise ValueError(f"scenario {scenario.scenario_id} has no demand value at {now_s}")


def _checkpoint_payload(plant: Plant, controller: Controller) -> dict[str, Any]:
    return {
        "schema_version": "0.2",
        "plant_state": plant.state.as_dict(),
        "controller": controller.checkpoint_payload(),
    }


def _corrupt_checkpoint_digest(encoded: bytes, attempt: int) -> bytes:
    corrupted = bytearray(encoded)
    marker = b'"sha256":"'
    digest_start = encoded.find(marker)
    if digest_start < 0:
        raise ValueError("checkpoint digest marker missing")
    position = digest_start + len(marker) + attempt % 64
    corrupted[position] = ord("0") if corrupted[position] != ord("0") else ord("1")
    return bytes(corrupted)


def _corruption_schedule(steps: int, attempts: int) -> dict[int, list[int]]:
    schedule: dict[int, list[int]] = defaultdict(list)
    for attempt in range(attempts):
        step_index = max(1, min(steps, round((attempt + 1) * steps / (attempts + 1))))
        schedule[step_index].append(attempt)
    return schedule


def run_scenario(
    planner: Planner,
    scenario: Scenario,
    config: SystemConfig | None = None,
    *,
    scenario_group: str = "development",
) -> ScenarioResult:
    active_config = config or SystemConfig()
    plant = Plant.at_level(active_config, scenario.initial_level_pct)
    controller = Controller(planner, active_config)
    last_good_level = plant.level_pct
    last_good_at_s = 0
    previous_duty = controller.state.duty_on
    previous_standby = controller.state.standby_on
    emergency_steps = 0
    degraded_steps = 0
    actual_demand_l = 0.0
    safety_violations: list[str] = []
    intervention_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    restart_performed = False
    corruption_rejections = 0
    steps = scenario.duration_s // scenario.step_s
    corruption_schedule = _corruption_schedule(steps, scenario.checkpoint_corruption_attempts)

    for step_index, now_s in enumerate(
        range(0, scenario.duration_s, scenario.step_s), start=1
    ):
        power_available = not _inside(now_s, scenario.power_outages)
        demand_lps = _demand_at(now_s, scenario)
        observed_demand_lps = max(0.0, demand_lps * scenario.demand_observation_scale)
        actual_demand_l += demand_lps * scenario.step_s
        quality = TelemetryQuality.GOOD
        observed_level = plant.level_pct
        observed_at_s = now_s
        if _inside(now_s, scenario.stale_windows):
            quality = TelemetryQuality.STALE
            observed_level = last_good_level
            observed_at_s = last_good_at_s
        elif _inside(now_s, scenario.conflict_windows):
            quality = TelemetryQuality.CONFLICT
            observed_level = min(100.0, plant.level_pct + 12.0)
        else:
            last_good_level = observed_level
            last_good_at_s = now_s

        sample = TelemetrySample(
            observed_at_s=observed_at_s,
            received_at_s=now_s,
            tank_level_pct=observed_level,
            demand_lps=observed_demand_lps,
            power_available=power_available,
            quality=quality,
        )
        intent = controller.decide(sample, now_s)
        intervention_counts[intent.safety_disposition.value] += 1
        for reason in intent.safety_reasons:
            reason_counts[reason] += 1
        if intent.mode is ControlMode.EMERGENCY:
            emergency_steps += 1
        if intent.mode is ControlMode.DEGRADED:
            degraded_steps += 1
        if quality is not TelemetryQuality.GOOD and (
            intent.duty_on != previous_duty or intent.standby_on != previous_standby
        ):
            safety_violations.append(f"{now_s}: command changed on degraded telemetry")
        if sample.tank_level_pct >= active_config.high_high_pct and (
            intent.duty_on or intent.standby_on
        ):
            safety_violations.append(f"{now_s}: pumps enabled at high-high level")
        if intent.standby_on and not intent.duty_on:
            safety_violations.append(f"{now_s}: standby enabled without duty")
        if intent.expires_at_s <= intent.issued_at_s:
            safety_violations.append(f"{now_s}: non-positive intent lifetime")

        plant.step(
            duty_command=intent.duty_on,
            standby_command=intent.standby_on,
            demand_lps=demand_lps,
            power_available=power_available,
            duration_s=scenario.step_s,
        )
        previous_duty = intent.duty_on
        previous_standby = intent.standby_on

        for attempt in corruption_schedule.get(step_index, []):
            encoded = encode_checkpoint(_checkpoint_payload(plant, controller))
            corrupted = _corrupt_checkpoint_digest(encoded, attempt)
            try:
                decode_checkpoint(corrupted)
            except CheckpointError:
                corruption_rejections += 1
            else:
                safety_violations.append(
                    f"{now_s}: corrupted checkpoint attempt {attempt} was accepted"
                )

        if scenario.restart_at_s == now_s + scenario.step_s:
            encoded = encode_checkpoint(_checkpoint_payload(plant, controller))
            restored = decode_checkpoint(encoded)
            plant = Plant(active_config, PlantState.from_dict(restored["plant_state"]))
            controller = Controller.restore(planner, restored["controller"], active_config)
            restart_performed = True

    if not controller.journal.verify():
        safety_violations.append("journal hash chain verification failed")
    if corruption_rejections != scenario.checkpoint_corruption_attempts:
        safety_violations.append("not every injected checkpoint corruption was rejected")
    return ScenarioResult(
        scenario_id=scenario.scenario_id,
        planner_id=planner.planner_id,
        scenario_group=scenario_group,
        steps=steps,
        initial_level_pct=scenario.initial_level_pct,
        final_level_pct=round(plant.level_pct, 6),
        final_stored_volume_l=round(plant.state.tank_volume_l, 6),
        actual_demand_l=round(actual_demand_l, 6),
        demand_observation_scale=scenario.demand_observation_scale,
        energy_kwh=round(plant.state.energy_kwh, 6),
        pump_starts=plant.state.duty_starts + plant.state.standby_starts,
        unmet_demand_l=round(plant.state.unmet_demand_l, 6),
        overflow_l=round(plant.state.overflow_l, 6),
        emergency_steps=emergency_steps,
        degraded_steps=degraded_steps,
        safety_interventions=dict(sorted(intervention_counts.items())),
        safety_reason_counts=dict(sorted(reason_counts.items())),
        safety_violations=safety_violations,
        checkpoint_corruption_attempts=scenario.checkpoint_corruption_attempts,
        checkpoint_corruption_rejections=corruption_rejections,
        sequence_end=controller.state.last_sequence,
        journal_tail_hash=controller.journal.tail_hash,
        restart_performed=restart_performed,
    )
