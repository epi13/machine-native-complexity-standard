# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import random

from water_control.model import Scenario

DEVELOPMENT_RANDOM_SEED = 20260727
DEVELOPMENT_RANDOM_COUNT = 16
PROTECTED_RANDOM_COUNT = 64


def selection_suite() -> tuple[Scenario, ...]:
    """Frozen epoch-2 selection scenarios; objective ratios are computed only here."""
    return (
        Scenario(
            scenario_id="normal-day",
            duration_s=43_200,
            step_s=60,
            initial_level_pct=60.0,
            demand_profile=(
                (0, 10_800, 2.2),
                (10_800, 21_600, 4.2),
                (21_600, 32_400, 3.0),
                (32_400, 43_200, 4.8),
            ),
        ),
        Scenario(
            scenario_id="peak-demand",
            duration_s=28_800,
            step_s=60,
            initial_level_pct=58.0,
            demand_profile=((0, 7_200, 3.5), (7_200, 24_000, 5.8), (24_000, 28_800, 3.0)),
        ),
        Scenario(
            scenario_id="power-outage",
            duration_s=28_800,
            step_s=60,
            initial_level_pct=70.0,
            demand_profile=((0, 28_800, 3.2),),
            power_outages=((7_200, 10_800),),
        ),
        Scenario(
            scenario_id="stale-telemetry",
            duration_s=21_600,
            step_s=60,
            initial_level_pct=55.0,
            demand_profile=((0, 21_600, 3.4),),
            stale_windows=((7_200, 9_000),),
        ),
        Scenario(
            scenario_id="conflicting-sensor",
            duration_s=21_600,
            step_s=60,
            initial_level_pct=55.0,
            demand_profile=((0, 21_600, 3.1),),
            conflict_windows=((5_400, 7_200),),
        ),
        Scenario(
            scenario_id="checkpoint-restart",
            duration_s=28_800,
            step_s=60,
            initial_level_pct=62.0,
            demand_profile=((0, 14_400, 3.0), (14_400, 28_800, 4.6)),
            restart_at_s=14_400,
        ),
    )


def combined_fault_suite() -> tuple[Scenario, ...]:
    return (
        Scenario(
            scenario_id="outage-plus-stale-telemetry",
            duration_s=28_800,
            step_s=60,
            initial_level_pct=68.0,
            demand_profile=((0, 28_800, 3.4),),
            power_outages=((7_200, 10_800),),
            stale_windows=((6_600, 11_400),),
        ),
        Scenario(
            scenario_id="restart-during-degraded-telemetry",
            duration_s=21_600,
            step_s=60,
            initial_level_pct=58.0,
            demand_profile=((0, 21_600, 3.2),),
            stale_windows=((7_200, 9_600),),
            restart_at_s=8_400,
        ),
        Scenario(
            scenario_id="near-empty-initial-storage",
            duration_s=21_600,
            step_s=60,
            initial_level_pct=18.0,
            demand_profile=((0, 7_200, 2.8), (7_200, 14_400, 3.6), (14_400, 21_600, 2.4)),
        ),
        Scenario(
            scenario_id="demand-model-error",
            duration_s=28_800,
            step_s=60,
            initial_level_pct=64.0,
            demand_profile=((0, 14_400, 4.2), (14_400, 28_800, 5.0)),
            demand_observation_scale=0.75,
        ),
        Scenario(
            scenario_id="repeated-checkpoint-corruption",
            duration_s=21_600,
            step_s=60,
            initial_level_pct=60.0,
            demand_profile=((0, 21_600, 3.5),),
            checkpoint_corruption_attempts=5,
        ),
    )


def randomized_suite(
    seed: int = DEVELOPMENT_RANDOM_SEED,
    count: int = DEVELOPMENT_RANDOM_COUNT,
    *,
    prefix: str = "randomized",
) -> tuple[Scenario, ...]:
    """Generate deterministic, bounded mixed-fault scenarios from a preserved seed."""
    rng = random.Random(seed)
    scenarios: list[Scenario] = []
    for index in range(count):
        duration_s = rng.choice((14_400, 18_000, 21_600, 25_200))
        segment_s = duration_s // 4
        demand_profile = tuple(
            (
                segment * segment_s,
                duration_s if segment == 3 else (segment + 1) * segment_s,
                round(rng.uniform(2.2, 4.8), 2),
            )
            for segment in range(4)
        )
        power_outages: tuple[tuple[int, int], ...] = ()
        stale_windows: tuple[tuple[int, int], ...] = ()
        conflict_windows: tuple[tuple[int, int], ...] = ()
        restart_at_s: int | None = None
        fault_mode = rng.randrange(6)
        if fault_mode in {1, 4}:
            start = rng.randrange(30, max(31, duration_s // 60 - 60)) * 60
            power_outages = ((start, min(duration_s, start + rng.choice((600, 1_200, 1_800)))),)
        if fault_mode in {2, 4, 5}:
            start = rng.randrange(20, max(21, duration_s // 60 - 50)) * 60
            stale_windows = ((start, min(duration_s, start + rng.choice((600, 1_200, 1_800)))),)
        if fault_mode == 3:
            start = rng.randrange(20, max(21, duration_s // 60 - 50)) * 60
            conflict_windows = (
                (start, min(duration_s, start + rng.choice((600, 1_200, 1_800)))),
            )
        if fault_mode == 5:
            stale_start, stale_end = stale_windows[0]
            restart_at_s = stale_start + min(600, (stale_end - stale_start) // 2)
            restart_at_s = (restart_at_s // 60) * 60
        scenarios.append(
            Scenario(
                scenario_id=f"{prefix}-{seed}-{index:02d}",
                duration_s=duration_s,
                step_s=60,
                initial_level_pct=round(rng.uniform(35.0, 75.0), 2),
                demand_profile=demand_profile,
                power_outages=power_outages,
                stale_windows=stale_windows,
                conflict_windows=conflict_windows,
                restart_at_s=restart_at_s,
                demand_observation_scale=round(rng.uniform(0.85, 1.15), 3),
                checkpoint_corruption_attempts=rng.choice((0, 0, 1, 2)),
            )
        )
    return tuple(scenarios)


def robustness_suite() -> tuple[Scenario, ...]:
    return combined_fault_suite() + randomized_suite()


def scenario_suite() -> tuple[Scenario, ...]:
    return selection_suite() + robustness_suite()


def protected_suite(seed: int) -> tuple[Scenario, ...]:
    return randomized_suite(seed, PROTECTED_RANDOM_COUNT, prefix="protected")


def smoke_suite() -> tuple[Scenario, ...]:
    selection = selection_suite()
    combined = combined_fault_suite()
    return selection[0], selection[3], selection[5], combined[0], combined[4]
