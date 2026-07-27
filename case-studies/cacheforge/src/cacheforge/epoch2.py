from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections.abc import Callable

from cacheforge.model import RequestTrace
from cacheforge.policies import EvictionPolicy, ReferenceLRU, SegmentedLRU
from cacheforge.scenarios import Scenario
from cacheforge.study import PolicyResult, evaluate_policy

CAPACITY_SWEEP = (16, 24, 32, 48)
DEVELOPMENT_SEEDS = tuple(range(1000, 1016))
REQUESTS_PER_SCENARIO = 48

AGGREGATE_RATIO_MAX = 0.98
MEDIAN_RATIO_MAX = 0.98
P95_RATIO_MAX = 1.05
WORST_RATIO_MAX = 1.06
IMPROVED_SCENARIO_FRACTION_MIN = 0.75


def generate_epoch2_scenario(seed: int, capacity_blocks: int) -> Scenario:
    if seed < 0:
        raise ValueError("seed must be non-negative")
    if capacity_blocks not in CAPACITY_SWEEP:
        raise ValueError(f"unsupported epoch-2 capacity: {capacity_blocks}")

    rng = random.Random(seed)
    tenants = tuple(f"tenant-{index}" for index in range(4))
    system_pool = ("assistant", "coding", "research", "analysis")
    hot_systems = system_pool[: 1 + seed % len(system_pool)]
    requests = []

    for index in range(REQUESTS_PER_SCENARIO):
        tenant = rng.choice(tenants)
        system = rng.choice(hot_systems) if rng.random() < 0.70 else f"cold-{seed}-{index // 4}"

        generated_blocks = rng.randint(1, 6)
        cancel_after = 1 if generated_blocks > 1 and rng.random() < 0.12 else None
        requests.append(
            RequestTrace(
                request_id=f"seed-{seed}-request-{index}",
                prompt_blocks=(
                    f"sys:{system}:0",
                    f"sys:{system}:1",
                    f"sys:{system}:2",
                    f"user:{tenant}:{index % 6}:0",
                    f"user:{tenant}:{index % 6}:1",
                ),
                generated_blocks=generated_blocks,
                cancel_after_generated=cancel_after,
            )
        )

    return Scenario(
        scenario_id=f"seeded-{seed}-capacity-{capacity_blocks}",
        capacity_blocks=capacity_blocks,
        requests=tuple(requests),
        purpose="paired seeded prefix-reuse, cancellation, and request-length stress",
    )


def epoch2_scenarios() -> tuple[Scenario, ...]:
    return tuple(
        generate_epoch2_scenario(seed, capacity)
        for seed in DEVELOPMENT_SEEDS
        for capacity in CAPACITY_SWEEP
    )


def _nearest_rank(values: list[float], percentile: float) -> float:
    if not values:
        return 1.0
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _metric(result: PolicyResult, scenario_id: str, name: str) -> int:
    return int(result.scenarios[scenario_id][name])


def summarize_policy_results(
    scenarios: tuple[Scenario, ...],
    lru: PolicyResult,
    segmented: PolicyResult,
    candidate: PolicyResult,
) -> dict[str, object]:
    observations: dict[str, dict[str, int | float | str]] = {}
    ratios: list[float] = []
    by_capacity: dict[int, dict[str, object]] = {}
    totals = {
        "lru_recomputed_blocks": 0,
        "segmented_lru_recomputed_blocks": 0,
        "candidate_recomputed_blocks": 0,
        "strongest_baseline_recomputed_blocks": 0,
    }
    improved = 0
    tied = 0
    regressed = 0

    for scenario in scenarios:
        scenario_id = scenario.scenario_id
        lru_recomputed = _metric(lru, scenario_id, "recomputed_blocks")
        segmented_recomputed = _metric(segmented, scenario_id, "recomputed_blocks")
        candidate_recomputed = _metric(candidate, scenario_id, "recomputed_blocks")
        strongest_recomputed = min(lru_recomputed, segmented_recomputed)
        ratio = candidate_recomputed / strongest_recomputed if strongest_recomputed else 1.0
        ratios.append(ratio)

        if candidate_recomputed < strongest_recomputed:
            relation = "IMPROVED"
            improved += 1
        elif candidate_recomputed == strongest_recomputed:
            relation = "TIED"
            tied += 1
        else:
            relation = "REGRESSED"
            regressed += 1

        observations[scenario_id] = {
            "capacity_blocks": scenario.capacity_blocks,
            "lru_recomputed_blocks": lru_recomputed,
            "segmented_lru_recomputed_blocks": segmented_recomputed,
            "candidate_recomputed_blocks": candidate_recomputed,
            "candidate_to_strongest_baseline_ratio": round(ratio, 6),
            "relation_to_strongest_baseline": relation,
        }

        totals["lru_recomputed_blocks"] += lru_recomputed
        totals["segmented_lru_recomputed_blocks"] += segmented_recomputed
        totals["candidate_recomputed_blocks"] += candidate_recomputed
        totals["strongest_baseline_recomputed_blocks"] += strongest_recomputed

        bucket = by_capacity.setdefault(
            scenario.capacity_blocks,
            {
                "scenario_count": 0,
                "lru_recomputed_blocks": 0,
                "segmented_lru_recomputed_blocks": 0,
                "candidate_recomputed_blocks": 0,
                "strongest_baseline_recomputed_blocks": 0,
                "ratios": [],
                "improved": 0,
                "tied": 0,
                "regressed": 0,
            },
        )
        bucket["scenario_count"] = int(bucket["scenario_count"]) + 1
        for name, value in (
            ("lru_recomputed_blocks", lru_recomputed),
            ("segmented_lru_recomputed_blocks", segmented_recomputed),
            ("candidate_recomputed_blocks", candidate_recomputed),
            ("strongest_baseline_recomputed_blocks", strongest_recomputed),
        ):
            bucket[name] = int(bucket[name]) + value
        bucket_ratios = bucket["ratios"]
        assert isinstance(bucket_ratios, list)
        bucket_ratios.append(ratio)
        bucket[relation.lower()] = int(bucket[relation.lower()]) + 1

    scenario_count = len(scenarios)
    aggregate_ratio = (
        totals["candidate_recomputed_blocks"] / totals["strongest_baseline_recomputed_blocks"]
        if totals["strongest_baseline_recomputed_blocks"]
        else 1.0
    )
    improved_fraction = improved / scenario_count if scenario_count else 0.0

    capacity_summary: dict[str, dict[str, int | float]] = {}
    all_capacity_aggregates_non_regressive = True
    for capacity, raw_bucket in sorted(by_capacity.items()):
        bucket_ratios = raw_bucket.pop("ratios")
        assert isinstance(bucket_ratios, list)
        candidate_total = int(raw_bucket["candidate_recomputed_blocks"])
        strongest_total = int(raw_bucket["strongest_baseline_recomputed_blocks"])
        capacity_ratio = candidate_total / strongest_total if strongest_total else 1.0
        all_capacity_aggregates_non_regressive &= capacity_ratio <= 1.0
        capacity_summary[str(capacity)] = {
            **{name: int(value) for name, value in raw_bucket.items()},
            "candidate_to_strongest_baseline_ratio": round(capacity_ratio, 6),
            "median_scenario_ratio": round(statistics.median(bucket_ratios), 6),
        }

    mean_ratio = statistics.mean(ratios) if ratios else 1.0
    median_ratio = statistics.median(ratios) if ratios else 1.0
    p95_ratio = _nearest_rank(ratios, 0.95)
    worst_ratio = max(ratios, default=1.0)
    gates = {
        "aggregate_ratio_at_most_0_98": aggregate_ratio <= AGGREGATE_RATIO_MAX,
        "median_ratio_at_most_0_98": median_ratio <= MEDIAN_RATIO_MAX,
        "p95_ratio_at_most_1_05": p95_ratio <= P95_RATIO_MAX,
        "worst_ratio_at_most_1_06": worst_ratio <= WORST_RATIO_MAX,
        "improved_scenario_fraction_at_least_0_75": improved_fraction
        >= IMPROVED_SCENARIO_FRACTION_MIN,
        "all_capacity_aggregates_non_regressive": all_capacity_aggregates_non_regressive,
        "candidate_used_no_fallback": int(candidate.aggregate["fallback_uses"]) == 0,
        "candidate_proposals_all_valid": int(candidate.aggregate["rejected_proposals"]) == 0,
    }
    observation_digest = hashlib.sha256(
        json.dumps(observations, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return {
        "status": "PASS" if all(gates.values()) else "FAIL",
        "gates": {name: "PASS" if passed else "FAIL" for name, passed in gates.items()},
        "aggregate": {
            **totals,
            "candidate_to_strongest_baseline_ratio": round(aggregate_ratio, 6),
            "mean_scenario_ratio": round(mean_ratio, 6),
            "median_scenario_ratio": round(median_ratio, 6),
            "p95_scenario_ratio": round(p95_ratio, 6),
            "worst_scenario_ratio": round(worst_ratio, 6),
            "improved_scenarios": improved,
            "tied_scenarios": tied,
            "regressed_scenarios": regressed,
            "improved_scenario_fraction": round(improved_fraction, 6),
            "candidate_fallback_uses": int(candidate.aggregate["fallback_uses"]),
            "candidate_rejected_proposals": int(candidate.aggregate["rejected_proposals"]),
        },
        "by_capacity": capacity_summary,
        "scenario_observation_digest": f"sha256:{observation_digest}",
    }


def evaluate_epoch2(
    candidate_factory: Callable[[], EvictionPolicy],
) -> dict[str, object]:
    scenarios = epoch2_scenarios()
    lru = evaluate_policy(ReferenceLRU, scenarios)
    segmented = evaluate_policy(SegmentedLRU, scenarios)
    candidate = evaluate_policy(candidate_factory, scenarios)
    summary = summarize_policy_results(scenarios, lru, segmented, candidate)
    return {
        "schema_version": "0.2",
        "study_id": "mncs.cacheforge.kv-cache.epoch-2-development.v1",
        "mode": "repository-visible-seeded-development",
        "development_result": summary["status"],
        "formal_mncs_status": "UNKNOWN",
        "formal_mncds_status": "UNKNOWN",
        "disposition": "REVIEW_REQUIRED",
        "promotion_authorized": False,
        "candidate_id": candidate.policy_id,
        "baseline_ids": [lru.policy_id, segmented.policy_id],
        "workload": {
            "seeds": list(DEVELOPMENT_SEEDS),
            "capacity_blocks": list(CAPACITY_SWEEP),
            "scenario_count": len(scenarios),
            "requests_per_scenario": REQUESTS_PER_SCENARIO,
            "total_requests": len(scenarios) * REQUESTS_PER_SCENARIO,
            "paired_capacity_sweep": True,
        },
        **summary,
        "limitations": [
            "All epoch-2 seeded scenarios remain repository-visible development evidence.",
            "The seeded generator is deterministic and is not a blind third-party holdout.",
            "The simulator does not execute a model or allocate accelerator memory.",
            "Candidate weights remain human-specified rather than learned from protected traces.",
            "A development PASS cannot promote formal MNCS or MNCDS status.",
        ],
    }
