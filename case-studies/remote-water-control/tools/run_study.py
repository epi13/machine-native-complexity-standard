#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
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
from water_control.model import SystemConfig  # noqa: E402
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



def write_deterministic_gzip(path: Path, payload: Any) -> None:
    data = (json.dumps(payload, indent=2) + "\n").encode()
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0) as compressed:
        compressed.write(data)
    path.write_bytes(buffer.getvalue())


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
     ²È="25åtè(€€€Í•¹…É¥½Ì€ôÍµ½­•}ÍÕ¥Ñ” ¤¥˜µ½‘”€ôô€‰Íµ½­”ˆ•±Í”Í•¹…É¥½}ÍÕ¥Ñ” ¤(€€€•Ù…±Õ…Ñ•€ô•Ù…±Õ…Ñ•}Í•¹…É¥½Ì¡Í•¹…É¥½Ì¤(€€€É½ÕÁ•€ô•Ù…±Õ…Ñ•‘l‰É½ÕÁ•‰t(€€€…¹‘¥‘…Ñ•}¥€ô•¹•É…Ñ•‘Q…‰±•A±…¹¹•È¹Á±…¹¹•É}¥(€€€‰…Í•±¥¹•}¥€ôI•…‘…‰±•	…Í•±¥¹•A±…¹¹•È¹Á±…¹¹•É}¥(€€€…¹‘¥‘…Ñ•}É•Á±…ä€ôl(€€€€€€€ÉÕ¹}Í•¹…É¥¼ (€€€€€€€€€€€•¹•É…Ñ•‘Q…‰±•A±…¹¹•È ¤°(€€€€€€€€€€€Í•¹…É¥¼°(€€€€€€€€€€€Í•¹…É¥½}É½ÕÀõ}Í•¹…É¥½}É½ÕÀ¡Í•¹…É¥¼¹Í•¹…É¥½}¥¤°(€€€€€€€€¤¹…Í}‘¥Ð ¤(€€€€€€€™½ÈÍ•¹…É¥¼¥¸Í•¹…É¥½Ì(€€€t(€€€‘•Ñ•Éµ¥¹¥ÍÑ¥}É•Á±…ä€ô…¹‘¥‘…Ñ•}É•Á±…ä€ôôÉ½ÕÁ•‘m…¹‘¥‘…Ñ•}¥‘t(€€€¡•­Á½¥¹Ñ}ÁÉ½‰”€ô¡•­Á½¥¹Ñ}½ÉÉÕÁÑ¥½¹}ÁÉ½‰” ¤(€€€Í¡•µ…}Ù…±¥‘…Ñ¥½¸€ôÙ…±¥‘…Ñ•}•áÁ•É¥µ•¹Ñ…±}É•½É‘Ì ¤(€€€½µÁ…É¥Í½¹Ì€ô•Ù…±Õ…Ñ•‘l‰½µÁ…É¥Í½¹Ì‰t(€€€Á•É}Í•¹…É¥½}Á…ÍÌ€ô…±°¡¥Ñ•µl‰ÍÑ…ÑÕÌ‰t€ôô€‰AMLˆ™½È¥Ñ•´¥¸½µÁ…É¥Í½¹Ì¤((€€€Í•¹…É¥½}‰å}¥€ôí¥Ñ•´¹Í•¹…É¥½}¥è¥Ñ•´™½È¥Ñ•´¥¸Í•¹…É¥½Íô(€€€Í•¹…É¥½}…Ñ•Í}Á…ÍÌ€ô…±° (€€€€€€€¹½ÐÉ•ÍÕ±Ñl‰Í…™•Ñå}Ù¥½±…Ñ¥½¹Ì‰t(€€€€€€€…¹É•ÍÕ±Ñl‰Í•ÅÕ•¹•}•¹‰t€ôôÉ•ÍÕ±Ñl‰ÍÑ•ÁÌ‰t(€€€€€€€…¹€ (€€€€€€€€€€€Í•¹…É¥½}‰å}¥‘mÉ•ÍÕ±Ñl‰Í•¹…É¥½}¥‰ut¹É•ÍÑ…ÉÑ}…Ñ}Ì¥Ì9½¹”(€€€€€€€€€€€½ÈÉ•ÍÕ±Ñl‰É•ÍÑ…ÉÑ}Á•É™½Éµ•‰t(€€€€€€€€¤(€€€€€€€…¹É•ÍÕ±Ñl‰¡•­Á½¥¹Ñ}½ÉÉÕÁÑ¥½¹}…ÑÑ•µÁÑÌ‰t(€€€€€€€€ôôÉ•ÍÕ±Ñl‰¡•­Á½¥¹Ñ}½ÉÉÕÁÑ¥½¹}É•©•Ñ¥½¹Ì‰t(€€€€€€€™½ÈÉ•ÍÕ±Ð¥¸É½ÕÁ•‘m…¹‘¥‘…Ñ•}¥‘t(€€€€¤((€€€Í•±•Ñ¥½¹}¥‘Ì€ôí¥Ñ•´¹Í•¹…É¥½}¥™½È¥Ñ•´¥¸Í•±•Ñ¥½¹}ÍÕ¥Ñ” ¥ô(€€€‰…Í•±¥¹•}Í•±•Ñ¥½¸€ôl(€€€€€€€¥Ñ•´™½È¥Ñ•´¥¸É½ÕÁ•‘m‰…Í•±¥¹•}¥‘t¥˜¥Ñ•µl‰Í•¹…É¥½}¥‰t¥¸Í•±•Ñ¥½¹}¥‘Ì(€€€t(€€€…¹‘¥‘…Ñ•}Í•±•Ñ¥½¸€ôl(€€€€€€€¥Ñ•´™½È¥Ñ•´¥¸É½ÕÁ•‘m…¹‘¥‘…Ñ•}¥‘t¥˜¥Ñ•µl‰Í•¹…É¥½}¥‰t¥¸Í•±•Ñ¥½¹}¥‘Ì(€€€t(€€€Í•±•Ñ¥½¹}½µÁ…É¥Í½¹Ì€ôl(€€€€€€€¥Ñ•´™½È¥Ñ•´¥¸½µÁ…É¥Í½¹Ì¥˜¥Ñ•µl‰Í•¹…É¥½}¥‰t¥¸Í•±•Ñ¥½¹}¥‘Ì(€€€t(€€€‰…Í•±¥¹•}…É•…Ñ”€ô…É•…Ñ”¡‰…Í•±¥¹•}Í•±•Ñ¥½¸¤(€€€…¹‘¥‘…Ñ•}…É•…Ñ”€ô…É•…Ñ”¡…¹‘¥‘…Ñ•}Í•±•Ñ¥½¸¤(€€€ÍÑ…ÉÑÍ}É…Ñ¥¼€ô…¹‘¥‘…Ñ•}…É•…Ñ•l‰ÁÕµÁ}ÍÑ…ÉÑÌ‰t€¼µ…à (€€€€€€€€Ä°‰…Í•±¥¹•}…É•…Ñ•l‰ÁÕµÁ}ÍÑ…ÉÑÌ‰t(€€€€¤(€€€É…Ý}•¹•Éå}É…Ñ¥¼€ô…¹‘¥‘…Ñ•}…É•…Ñ•l‰•¹•Éå}­Ý ‰t€¼µ…à (€€€€€€€€À¸ÀÀÀÀÀÄ°‰…Í•±¥¹•}…É•…Ñ•l‰•¹•Éå}­Ý ‰t(€€€€¤(€€€¹½Éµ…±¥é•‘}•¹•Éå}É…Ñ¥¼€ôÍÕ´ (€€€€€€€™±½…Ð¡¥Ñ•µl‰…¹‘¥‘…Ñ•}¥¹Ù•¹Ñ½Éå}…‘©ÕÍÑ•‘}•¹•Éå}­Ý ‰t¤(€€€€€€€™½È¥Ñ•´¥¸Í•±•Ñ¥½¹}½µÁ…É¥Í½¹Ì(€€€€¤€¼µ…à À¸ÀÀÀÀÀÄ°‰…Í•±¥¹•}…É•…Ñ•l‰•¹•Éå}­Ý ‰t¤(€€€½‰©•Ñ¥Ù•}Á…ÍÌ€ôµ½‘”€ôô€‰Íµ½­”ˆ½È€ (€€€€€€€ÍÑ…ÉÑÍ}É…Ñ¥¼€ðôM1Q%=9}5a}AU5A}MQIQ}IQ%<(€€€€€€€…¹É…Ý}•¹•Éå}É…Ñ¥¼€ðôM1Q%=9}5a}I]}9Ie}IQ%<(€€€€€€€…¹¹½Éµ…±¥é•‘}•¹•Éå}É…Ñ¥¼€ðô5a}%9Y9Q=Ie})UMQ}9Ie}IQ%<(€€€€€€€…¹…¹‘¥‘…Ñ•}…É•…Ñ•l‰Õ¹µ•Ñ}‘•µ…¹‘}°‰t€ðô‰…Í•±¥¹•}…É•…Ñ•l‰Õ¹µ•Ñ}‘•µ…¹‘}°‰t(€€€€€€€…¹…¹‘¥‘…Ñ•}…É•…Ñ•l‰½Ù•É™±½Ý}°‰t€ðô‰…Í•±¥¹•}…É•…Ñ•l‰½Ù•É™±½Ý}°‰t(€€€€¤(€€€¡…É‘}…Ñ•Í}Á…ÍÌ€ô€ (€€€€€€€Í•¹…É¥½}…Ñ•Í}Á…ÍÌ(€€€€€€€…¹‘•Ñ•Éµ¥¹¥ÍÑ¥}É•Á±…ä(€€€€€€€…¹¡•­Á½¥¹Ñ}ÁÉ½‰•l‰ÍÑ…ÑÕÌ‰t€ôô€‰AMLˆ(€€€€€€€…¹Í¡•µ…}Ù…±¥‘…Ñ¥½¹l‰ÍÑ…ÑÕÌ‰t€ôô€‰AMLˆ(€€€€€€€…¹Á•É}Í•¹…É¥½}Á…ÍÌ(€€€€¤(€€€‘•Ù•±½Áµ•¹Ñ}Á…ÍÌ€ô¡…É‘}…Ñ•Í}Á…ÍÌ…¹½‰©•Ñ¥Ù•}Á…ÍÌ(€€€…±±}…É•…Ñ•Ì€ôì(€€€€€€€€‰‰…Í•±¥¹”ˆè…É•…Ñ”¡É½ÕÁ•‘m‰…Í•±¥¹•}¥‘t¤°(€€€€€€€€‰…¹‘¥‘…Ñ”ˆè…É•…Ñ”¡É½ÕÁ•‘m…¹‘¥‘…Ñ•}¥‘t¤°(€€€ô(€€€ÍÕµµ…Éä€ôì(€€€€€€€€‰Í¡•µ…}Ù•ÉÍ¥½¸ˆè€ˆÀ¸Èˆ°(€€€€€€€€‰ÍÑÕ‘å}¥ˆè€‰µ¹Ì¹É•µ½Ñ”µÝ…Ñ•Èµ½¹ÑÉ½°¹‘•Ù•±½Áµ•¹Ðµ•Á½ ´Èˆ°(€€€€€€€€‰µ½‘”ˆèµ½‘”°(€€€€€€€€‰‘•Ù•±½Áµ•¹Ñ}É•ÍÕ±Ðˆè€‰AMLˆ¥˜‘•Ù•±½Áµ•¹Ñ}Á…ÍÌ•±Í”€‰%0ˆ°(€€€€€€€€‰™½Éµ…±}µ¹Í}ÍÑ…ÑÕÌˆè€‰U9-9=]8ˆ°(€€€€€€€€‰™½Éµ…±}µ¹‘Í}ÍÑ…ÑÕÌˆè€‰U9-9=]8ˆ°(€€€€€€€€‰‘¥ÍÁ½Í¥Ñ¥½¸ˆè€‰IY%]}IEU%Iˆ°(€€€€€€€€‰±…¥µ}¹½Ñ”ˆè€ (€€€€€€€€€€€€‰Q¡¥Ì‘•Ù•±½Áµ•¹ÐÉÕ¸‘½•Ì¹½Ð±…¥´59Lµ0Ô½È59LµÌ¸Q¡”•Ù…±Õ…Ñ½Èµ±½­•€ˆ(€€€€€€€€€€€€‰É½ÍÌµ¡½ÍÐÝ½É­™±½Ü¥ÌÁÉ½Ñ•Ñ•…Ð•á•ÕÑ¥½¸Ñ¥µ”‰ÕÐ¥Ì¹½Ð…¸¥¹‘•Á•¹‘•¹Ð€ˆ(€€€€€€€€€€€€‰Ñ¡¥ÉµÁ…ÉÑä•Ù…±Õ…Ñ¥½¸°É•±•…Í”‰¥¹‘¥¹œ°½È½Á•É…Ñ¥½¹…°•Ù¥‘•¹”¸ˆ(€€€€€€€€¤°(€€€€€€€€‰Í•¹…É¥½}½Õ¹ÑÌˆèì(€€€€€€€€€€€€‰Í•±•Ñ¥½¸ˆè±•¸¡Í•±•Ñ¥½¹}ÍÕ¥Ñ” ¤¤°(€€€€€€€€€€€€‰½µ‰¥¹•‘}™…Õ±Ðˆè±•¸¡½µ‰¥¹•‘}™…Õ±Ñ}ÍÕ¥Ñ” ¤¤°(€€€€€€€€€€€€‰É…¹‘½µ¥é•ˆè±•¸¡É…¹‘½µ¥é•‘}ÍÕ¥Ñ” ¤¤°(€€€€€€€€€€€€‰•Ù…±Õ…Ñ•ˆè±•¸¡Í•¹…É¥½Ì¤°(€€€€€€€ô°(€€€€€€€€‰¡…É‘}…Ñ•Ìˆèì(€€€€€€€€€€€€‰Í•¹…É¥½}Í…™•Ñäˆè€‰AMLˆ¥˜Í•¹…É¥½}…Ñ•Í}Á…ÍÌ•±Í”€‰%0ˆ°(€€€€€€€€€€€€‰Á•É}Í•¹…É¥½}É•É•ÍÍ¥½¸ˆè€‰AMLˆ¥˜Á•É}Í•¹…É¥½}Á…ÍÌ•±Í”€‰%0ˆ°(€€€€€€€€€€€€‰‘•Ñ•Éµ¥¹¥ÍÑ¥}É•Á±…äˆè€‰AMLˆ¥˜‘•Ñ•Éµ¥¹¥ÍÑ¥}É•Á±…ä•±Í”€‰%0ˆ°(€€€€€€€€€€€€‰¡•­Á½¥¹Ñ}½ÉÉÕÁÑ¥½¹}É•©•Ñ¥½¸ˆè¡•­Á½¥¹Ñ}ÁÉ½‰•l‰ÍÑ…ÑÕÌ‰t°(€€€€€€€€€€€€‰•áÁ•É¥µ•¹Ñ…±}Í¡•µ…}Ù…±¥‘…Ñ¥½¸ˆèÍ¡•µ…}Ù…±¥‘…Ñ¥½¹l‰ÍÑ…ÑÕÌ‰t°(€€€€€€€ô°(€€€€€€€€‰¡•­Á½¥¹Ñ}ÁÉ½‰”ˆè¡•­Á½¥¹Ñ}ÁÉ½‰”°(€€€€€€€€‰Í¡•µ…}Ù…±¥‘…Ñ¥½¸ˆèÍ¡•µ…}Ù…±¥‘…Ñ¥½¸°(€€€€€€€€‰½‰©•Ñ¥Ù”ˆèì(€€€€€€€€€€€€‰ÍÑ…ÑÕÌˆè€‰AMLˆ¥˜½‰©•Ñ¥Ù•}Á…ÍÌ•±Í”€‰%0ˆ°(€€€€€€€€€€€€‰Í½Á”ˆè€‰™É½é•¸Í•±•Ñ¥½¸Í•¹…É¥½Ì½¹±äˆ°(€€€€€€€€€€€€‰…¹‘¥‘…Ñ•}Ñ½}‰…Í•±¥¹•}ÁÕµÁ}ÍÑ…ÉÑ}É…Ñ¥¼ˆèÉ½Õ¹¡ÍÑ…ÉÑÍ}É…Ñ¥¼°€Ø¤°(€€€€€€€€€€€€‰…¹‘¥‘…Ñ•}Ñ½}‰…Í•±¥¹•}É…Ý}•¹•Éå}É…Ñ¥¼ˆèÉ½Õ¹¡É…Ý}•¹•Éå}É…Ñ¥¼°€Ø¤°(€€€€€€€€€€€€‰…¹‘¥‘…Ñ•}Ñ½}‰…Í•±¥¹•}¥¹Ù•¹Ñ½Éå}…‘©ÕÍÑ•‘}•¹•Éå}É…Ñ¥¼ˆèÉ½Õ¹ (€€€€€€€€€€€€€€€¹½Éµ…±¥é•‘}•¹•Éå}É…Ñ¥¼°€Ø(€€€€€€€€€€€€¤°(€€€€€€€€€€€€‰É•ÅÕ¥É•‘}ÁÕµÁ}ÍÑ…ÉÑ}É…Ñ¥½}µ…àˆèM1Q%=9}5a}AU5A}MQIQ}IQ%<°(€€€€€€€€€€€€‰É•ÅÕ¥É•‘}É…Ý}•¹•Éå}É…Ñ¥½}µ…àˆèM1Q%=9}5a}I]}9Ie}IQ%<°(€€€€€€€€€€€€‰É•ÅÕ¥É•‘}¥¹Ù•¹Ñ½Éå}…‘©ÕÍÑ•‘}•¹•Éå}É…Ñ¥½}µ…àˆè5a}%9Y9Q=Ie})UMQ}9Ie}IQ%<°(€€€€€€€ô°(€€€€€€€€‰Í•±•Ñ¥½¹}…É•…Ñ•Ìˆèì(€€€€€€€€€€€€‰‰…Í•±¥¹”ˆè‰…Í•±¥¹•}…É•…Ñ”°(€€€€€€€€€€€€‰…¹‘¥‘…Ñ”ˆè…¹‘¥‘…Ñ•}…É•…Ñ”°(€€€€€€€ô°(€€€€€€€€‰…±±}Í•¹…É¥½}…É•…Ñ•Ìˆè…±±}…É•…Ñ•Ì°(€€€€€€€€‰Á•É}Í•¹…É¥½}½µÁ…É¥Í½¹Ìˆè½µÁ…É¥Í½¹Ì°(€€€€€€€€‰•Ù¥‘•¹•}‘¥•ÍÑÌˆèì(€€€€€€€€€€€€‰Í•¹…É¥½}‘•™¥¹¥Ñ¥½¹Ìˆè…¹½¹¥…±}Í¡„ÈÔØ¡m¥Ñ•´¹…Í}‘¥Ð ¤™½È¥Ñ•´¥¸Í•¹…É¥½Ít¤°(€€€€€€€€€€€€‰½µÁ…É¥Í½¹Ìˆè…¹½¹¥…±}Í¡„ÈÔØ¡½µÁ…É¥Í½¹Ì¤°(€€€€€€€ô°(€€€€€€€€‰¥‘•¹Ñ¥Ñ¥•Ìˆèì(€€€€€€€€€€€€‰Á±…¹¹•É}ÍÁ•ŒˆèÍ¡„ÈÔØ¡I==P€¼€‰•¹•É…Ñ½Èˆ€¼€‰Á±…¹¹•ÈµÍÁ•Œ¹©Í½¸ˆ¤°(€€€€€€€€€€€€‰•¹•É…Ñ•‘}Á±…¹¹•ÈˆèÍ¡„ÈÔØ¡I==P€¼€‰µ…¡¥¹”ˆ€¼€‰•¹•É…Ñ•‘}Á±…¹¹•È¹Áäˆ¤°(€€€€€€€€€€€€‰Í…™•Ñå}­•É¹•°ˆèÍ¡„ÈÔØ¡I==P€¼€‰ÍÉŒˆ€¼€‰Ý…Ñ•É}½¹ÑÉ½°ˆ€¼€‰Í…™•Ñä¹Áäˆ¤°(€€€€€€€€€€€€‰Í¥µÕ±…Ñ½ÈˆèÍ¡„ÈÔØ¡I==P€¼€‰ÍÉŒˆ€¼€‰Ý…Ñ•É}½¹ÑÉ½°ˆ€¼€‰Í¥µÕ±…Ñ½È¹Áäˆ¤°(€€€€€€€€€€€€‰Í•¹…É¥½ÌˆèÍ¡„ÈÔØ¡I==P€¼€‰ÍÉŒˆ€¼€‰Ý…Ñ•É}½¹ÑÉ½°ˆ€¼€‰Í•¹…É¥½Ì¹Áäˆ¤°(€€€€€€€€€€€€‰ÁÉ•É•¥ÍÑÉ…Ñ¥½¸ˆèÍ¡„ÈÔØ¡I==P€¼€‰ÁÉ•É•¥ÍÑÉ…Ñ¥½¸¹©Í½¸ˆ¤°(€€€€€€€ô°(€€€€€€€€‰±¥µ¥Ñ…Ñ¥½¹Ìˆèl(€€€€€€€€€€€€‰•Ù•±½Áµ•¹ÐÍ•¹…É¥½Ì…¹‘•Ñ•Éµ¥¹¥ÍÑ¥ŒÉ…¹‘½µ¥é•Í••‘Ì…É”É•Á½Í¥Ñ½ÉäÙ¥Í¥‰±”¸ˆ°(€€€€€€€€€€€€‰%¹Ù•¹Ñ½Éä¹½Éµ…±¥é…Ñ¥½¸ÕÍ•ÌÑ¡”‘•±…É•‘ÕÑäµÁÕµÀµ…É¥¹…°•¹•ÉäÁ•ÈÍÑ½É•±¥Ñ•Èì¥Ð¥Ì¹½Ð„ÁÕµÀµÕÉÙ”µ½‘•°¸ˆ°(€€€€€€€€€€€€‰Q¡”Á±…¹Ðµ½‘•°¥Ì„‰½Õ¹‘•‘¥¥Ñ…°ÑÝ¥¸…¹¥Ì¹½Ð„¡å‘É…Õ±¥Œ‘•Í¥¸µ½‘•°¸ˆ°(€€€€€€€€€€€€‰9¼±¥Ù”A1°M°ÁÕµÀ°Ù…±Ù”°½È™¥•±¹•ÑÝ½É¬¥Ì½¹¹•Ñ•¸ˆ°(€€€€€€€€€€€€‰Q¡”•¹•É…Ñ•Á±…¹¹•È¥Ì„‘•Ù•±½Áµ•¹Ð…¹‘¥‘…Ñ”°¹½Ð…¸…•ÁÑ•É•±•…Í”…ÉÑ¥™…Ð¸ˆ°(€€€€€€€€€€€€‰%¹‘•Á•¹‘•¹Ð‘½µ…¥¸É•Ù¥•Ü°É•±•…Í”…ÕÑ¡½É¥Ñä°…¹½Á•É…Ñ¥½¹…°±¥™•å±”•Ù¥‘•¹”É•µ…¥¸½Á•¸¸ˆ°(€€€€€€€t°(€€€ô(€€€¥˜µ½‘”€ôô€‰…±°ˆè(€€€€€€€½ÕÑÁÕÐ€ôI==P€¼€‰•Ù¥‘•¹”ˆ€¼€‰É•ÍÕ±ÑÌˆ(€€€€€€€½ÕÑÁÕÐ¹µ­‘¥È¡Á…É•¹ÑÌõQÉÕ”°•á¥ÍÑ}½¬õQÉÕ”¤(€€€€€€€ÝÉ¥Ñ•}‘•Ñ•Éµ¥¹¥ÍÑ¥}é¥À (€€€€€€€€€€€½ÕÑÁÕÐ€¼€‰Í•¹…É¥¼µÉ•ÍÕ±ÑÌ¹©Í½¸¹èˆ°(€€€€€€€€€€€ì‰Í¡•µ…}Ù•ÉÍ¥½¸ˆè€ˆÀ¸Èˆ°€‰É•ÍÕ±ÑÌˆè•Ù…±Õ…Ñ•‘l‰½‰Í•ÉÙ…Ñ¥½¹Ì‰uô°(€€€€€€€€¤(€€€€€€€ÝÉ¥Ñ•}‘•Ñ•Éµ¥¹¥ÍÑ¥}é¥À¡½ÕÑÁÕÐ€¼€‰ÍÑÕ‘äµÍÕµµ…Éä¹©Í½¸¹èˆ°ÍÕµµ…Éä¤(€€€É•ÑÕÉ¸ÍÕµµ…Éä(()‘•˜µ…¥¸ ¤€´ø¥¹Ðè(€€€Á…ÉÍ•È€ô…ÉÁ…ÉÍ”¹ÉÕµ•¹ÑA…ÉÍ•È ¤(€€€Á…ÉÍ•È¹…‘‘}…ÉÕµ•¹Ð ‰µ½‘”ˆ°¡½¥•Ìô ‰Íµ½­”ˆ°€‰…±°ˆ¤°¹…ÉÌôˆüˆ°‘•™…Õ±Ðô‰Íµ½­”ˆ¤(€€€…ÉÌ€ôÁ…ÉÍ•È¹Á…ÉÍ•}…ÉÌ ¤(€€€ÍÕµµ…Éä€ôÉÕ¸¡…ÉÌ¹µ½‘”¤(€€€ÁÉ¥¹Ð¡©Í½¸¹‘ÕµÁÌ¡ÍÕµµ…Éä°¥¹‘•¹ÐôÈ¤¤(€€€É•ÑÕÉ¸€À¥˜ÍÕµµ…Éål‰‘•Ù•±½Áµ•¹Ñ}É•ÍÕ±Ð‰t€ôô€‰AMLˆ•±Í”€Ä(()¥˜}}¹…µ•}|€ôô€‰}}µ…¥¹}|ˆè(€€€É…¥Í”MåÍÑ•µá¥Ð¡µ…¥¸ ¤¤