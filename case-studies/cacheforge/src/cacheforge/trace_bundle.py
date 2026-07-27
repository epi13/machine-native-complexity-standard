from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cacheforge.epoch2 import summarize_policy_results
from cacheforge.model import RequestTrace
from cacheforge.policies import EvictionPolicy, ReferenceLRU, SegmentedLRU
from cacheforge.scenarios import Scenario
from cacheforge.study import evaluate_policy

MAX_SCENARIOS = 256
MAX_REQUESTS = 10_000


@dataclass(frozen=True)
class TraceBundle:
    bundle_id: str
    input_digest: str
    scenarios: tuple[Scenario, ...]


def _require_mapping(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _require_list(value: object, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def load_trace_bundle(path: Path) -> TraceBundle:
    raw = path.read_bytes()
    payload = _require_mapping(json.loads(raw), "trace bundle")
    if payload.get("schema_version") != "0.1":
        raise ValueError("unsupported trace bundle schema")

    bundle_id = payload.get("bundle_id")
    if not isinstance(bundle_id, str) or not bundle_id:
        raise ValueError("bundle_id must be a non-empty string")

    raw_scenarios = _require_list(payload.get("scenarios"), "scenarios")
    if not raw_scenarios or len(raw_scenarios) > MAX_SCENARIOS:
        raise ValueError("scenario count is outside the allowed range")

    scenarios: list[Scenario] = []
    seen_scenario_ids: set[str] = set()
    total_requests = 0

    for raw_scenario in raw_scenarios:
        scenario_payload = _require_mapping(raw_scenario, "scenario")
        scenario_id = scenario_payload.get("scenario_id")
        if not isinstance(scenario_id, str) or not scenario_id:
            raise ValueError("scenario_id must be a non-empty string")
        if scenario_id in seen_scenario_ids:
            raise ValueError(f"duplicate scenario_id: {scenario_id}")
        seen_scenario_ids.add(scenario_id)

        capacity_blocks = scenario_payload.get("capacity_blocks")
        if not isinstance(capacity_blocks, int) or capacity_blocks < 1:
            raise ValueError("capacity_blocks must be a positive integer")

        raw_requests = _require_list(scenario_payload.get("requests"), "requests")
        if not raw_requests:
            raise ValueError(f"scenario {scenario_id} has no requests")

        requests: list[RequestTrace] = []
        seen_request_ids: set[str] = set()
        for raw_request in raw_requests:
            request_payload = _require_mapping(raw_request, "request")
            request_id = request_payload.get("request_id")
            if not isinstance(request_id, str) or not request_id:
                raise ValueError("request_id must be a non-empty string")
            if request_id in seen_request_ids:
                raise ValueError(f"duplicate request_id in scenario {scenario_id}: {request_id}")
            seen_request_ids.add(request_id)

            prompt_blocks = _require_list(request_payload.get("prompt_blocks"), "prompt_blocks")
            if not prompt_blocks or not all(
                isinstance(block, str) and block for block in prompt_blocks
            ):
                raise ValueError("prompt_blocks must contain non-empty strings")

            generated_blocks = request_payload.get("generated_blocks")
            if not isinstance(generated_blocks, int):
                raise ValueError("generated_blocks must be an integer")

            cancel_after = request_payload.get("cancel_after_generated")
            if cancel_after is not None and not isinstance(cancel_after, int):
                raise ValueError("cancel_after_generated must be an integer or null")

            requests.append(
                RequestTrace(
                    request_id=request_id,
                    prompt_blocks=tuple(prompt_blocks),
                    generated_blocks=generated_blocks,
                    priority=int(request_payload.get("priority", 1)),
                    cancel_after_generated=cancel_after,
                )
            )

        total_requests += len(requests)
        if total_requests > MAX_REQUESTS:
            raise ValueError("trace bundle exceeds the request limit")

        purpose = scenario_payload.get("purpose", "external protected evaluation")
        if not isinstance(purpose, str):
            raise ValueError("purpose must be a string")
        scenarios.append(
            Scenario(
                scenario_id=scenario_id,
                capacity_blocks=capacity_blocks,
                requests=tuple(requests),
                purpose=purpose,
            )
        )

    digest = hashlib.sha256(raw).hexdigest()
    return TraceBundle(
        bundle_id=bundle_id,
        input_digest=f"sha256:{digest}",
        scenarios=tuple(scenarios),
    )


def evaluate_trace_bundle(
    bundle: TraceBundle,
    candidate_factory: Callable[[], EvictionPolicy],
) -> dict[str, object]:
    lru = evaluate_policy(ReferenceLRU, bundle.scenarios)
    segmented = evaluate_policy(SegmentedLRU, bundle.scenarios)
    candidate = evaluate_policy(candidate_factory, bundle.scenarios)
    observations = summarize_policy_results(
        bundle.scenarios,
        lru,
        segmented,
        candidate,
    )
    return {
        "schema_version": "0.2",
        "study_id": "mncs.cacheforge.kv-cache.protected-evaluation.v1",
        "mode": "external-trace-bundle",
        "bundle_id": bundle.bundle_id,
        "input_bundle_digest": bundle.input_digest,
        "observed_gate_result": observations["status"],
        "formal_mncs_status": "UNKNOWN",
        "formal_mncds_status": "UNKNOWN",
        "disposition": "REVIEW_REQUIRED",
        "promotion_authorized": False,
        "candidate_id": candidate.policy_id,
        "baseline_ids": [lru.policy_id, segmented.policy_id],
        "scenario_count": len(bundle.scenarios),
        **observations,
        "limitations": [
            "The evaluator records observations but cannot promote a formal claim.",
            "Trace custody and independence must be reviewed outside this process.",
            "A real inference-server adapter and accelerator evidence remain outstanding.",
        ],
    }
