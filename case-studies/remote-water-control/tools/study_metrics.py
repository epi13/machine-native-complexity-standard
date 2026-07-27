# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

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

from water_control.checkpoint import (  # noqa: E402
    CheckpointError,
    decode_checkpoint,
    encode_checkpoint,
)
from water_control.model import SystemConfig  # noqa: E402

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
        "unmet_demand_l": round(
            sum(float(item["unmet_demand_l"]) for item in results), 6
        ),
        "overflow_l": round(sum(float(item["overflow_l"]) for item in results), 6),
        "safety_violations": sum(
            len(item["safety_violations"]) for item in results
        ),
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
    terminal_inventory_delta_l = float(candidate["final_stored_volume_l"]) - float(
        baseline["final_stored_volume_l"]
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
        "inventory_adjusted_energy": (
            adjusted_ratio <= MAX_INVENTORY_ADJUSTED_ENERGY_RATIO
        ),
        "pump_start_regression": (
            int(candidate["pump_starts"])
            <= int(baseline["pump_starts"]) + MAX_PUMP_START_INCREASE
        ),
        "terminal_reserve": terminal_level_delta >= MIN_TERMINAL_LEVEL_DELTA_PCT,
        "unmet_demand": (
            float(candidate["unmet_demand_l"])
            <= float(baseline["unmet_demand_l"])
        ),
        "overflow": (
            float(candidate["overflow_l"]) <= float(baseline["overflow_l"])
        ),
        "candidate_safety": not candidate["safety_violations"],
        "checkpoint_corruption_rejection": (
            int(candidate["checkpoint_corruption_rejections"])
            == int(candidate["checkpoint_corruption_attempts"])
        ),
    }
    return {
        "scenario_id": candidate["scenario_id"],
        "scenario_group": candidate["scenario_group"],
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": {
            key: "PASS" if value else "FAIL" for key, value in checks.items()
        },
        "candidate_to_baseline_inventory_adjusted_energy_ratio": round(
            adjusted_ratio, 6
        ),
        "candidate_inventory_adjusted_energy_kwh": round(
            adjusted_candidate_energy, 6
        ),
        "candidate_to_baseline_raw_energy_ratio": round(
            float(candidate["energy_kwh"]) / max(0.000001, baseline_energy), 6
        ),
        "candidate_pump_start_delta": (
            int(candidate["pump_starts"]) - int(baseline["pump_starts"])
        ),
        "candidate_terminal_level_delta_pct": round(terminal_level_delta, 6),
        "terminal_inventory_delta_l": round(terminal_inventory_delta_l, 6),
        "limits": {
            "inventory_adjusted_energy_ratio_max": (
                MAX_INVENTORY_ADJUSTED_ENERGY_RATIO
            ),
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
        corrupted[position] = (
            ord("0") if corrupted[position] != ord("0") else ord("1")
        )
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
        (
            "mncs-contract-profile.schema.json",
            ROOT / "contract" / "contract-profile.json",
        ),
        ("mncs-assurance-case.schema.json", ROOT / "assurance-case.json"),
    )
    failures: list[str] = []
    for schema_name, record_path in checks:
        schema = json.loads(
            (REPOSITORY_ROOT / "schemas" / schema_name).read_text()
        )
        record = json.loads(record_path.read_text())
        errors = sorted(
            Draft202012Validator(schema).iter_errors(record),
            key=lambda item: item.path,
        )
        failures.extend(
            f"{record_path.name}: {error.message}" for error in errors
        )
    return {"status": "FAIL" if failures else "PASS", "failures": failures}
