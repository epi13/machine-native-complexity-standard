# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from water_control.model import Scenario


def scenario_suite() -> tuple[Scenario, ...]:
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


def smoke_suite() -> tuple[Scenario, ...]:
    scenarios = scenario_suite()
    return scenarios[0], scenarios[3], scenarios[5]
