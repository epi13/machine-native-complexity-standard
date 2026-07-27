from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "machine"))

from cacheforge.epoch2 import (  # noqa: E402
    CAPACITY_SWEEP,
    DEVELOPMENT_SEEDS,
    epoch2_scenarios,
    evaluate_epoch2,
    generate_epoch2_scenario,
)
from cacheforge.trace_bundle import (  # noqa: E402
    evaluate_trace_bundle,
    load_trace_bundle,
)
from generated_policy import GeneratedEvictionPolicy  # noqa: E402


def _bundle_payload() -> dict[str, object]:
    return {
        "schema_version": "0.1",
        "bundle_id": "cacheforge.test.external.v1",
        "scenarios": [
            {
                "scenario_id": "external-small",
                "capacity_blocks": 16,
                "purpose": "test external bundle",
                "requests": [
                    {
                        "request_id": "request-0",
                        "prompt_blocks": [
                            "sys:shared:0",
                            "sys:shared:1",
                            "user:a:0",
                        ],
                        "generated_blocks": 2,
                    },
                    {
                        "request_id": "request-1",
                        "prompt_blocks": [
                            "sys:shared:0",
                            "sys:shared:1",
                            "user:b:0",
                        ],
                        "generated_blocks": 2,
                        "cancel_after_generated": 1,
                    },
                ],
            }
        ],
    }


def test_epoch2_workload_is_deterministic_and_paired() -> None:
    first = generate_epoch2_scenario(DEVELOPMENT_SEEDS[0], CAPACITY_SWEEP[0])
    second = generate_epoch2_scenario(DEVELOPMENT_SEEDS[0], CAPACITY_SWEEP[-1])
    assert first.requests == second.requests
    assert first.capacity_blocks != second.capacity_blocks

    scenarios = epoch2_scenarios()
    assert len(scenarios) == len(DEVELOPMENT_SEEDS) * len(CAPACITY_SWEEP)
    assert len({scenario.scenario_id for scenario in scenarios}) == len(scenarios)


def test_epoch2_candidate_meets_frozen_development_gates() -> None:
    result = evaluate_epoch2(GeneratedEvictionPolicy)
    assert result["development_result"] == "PASS", json.dumps(result, indent=2)
    assert result["formal_mncs_status"] == "UNKNOWN"
    assert result["promotion_authorized"] is False
    assert result["aggregate"]["candidate_recomputed_blocks"] == 39654
    assert result["aggregate"]["strongest_baseline_recomputed_blocks"] == 41167
    assert result["aggregate"]["improved_scenarios"] == 53
    assert result["scenario_observation_digest"] == (
        "sha256:23dace9d5e3b537c4aef930ddf512475c6924f14bb0c603fcf59d852b831f897"
    )


def test_external_trace_bundle_never_auto_promotes(tmp_path: Path) -> None:
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(_bundle_payload(), sort_keys=True))
    bundle = load_trace_bundle(bundle_path)
    result = evaluate_trace_bundle(bundle, GeneratedEvictionPolicy)
    assert result["bundle_id"] == "cacheforge.test.external.v1"
    assert result["promotion_authorized"] is False
    assert result["formal_mncs_status"] == "UNKNOWN"
    assert result["disposition"] == "REVIEW_REQUIRED"


def test_external_trace_bundle_rejects_duplicate_request_ids(tmp_path: Path) -> None:
    payload = _bundle_payload()
    scenario = payload["scenarios"][0]
    assert isinstance(scenario, dict)
    requests = scenario["requests"]
    assert isinstance(requests, list)
    duplicate = dict(requests[0])
    requests.append(duplicate)

    bundle_path = tmp_path / "duplicate.json"
    bundle_path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="duplicate request_id"):
        load_trace_bundle(bundle_path)
