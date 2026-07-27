#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT.parents[1]
REMOTE_ROOT = REPOSITORY_ROOT / "case-studies" / "remote-water-control"
sys.path.insert(0, str(REMOTE_ROOT / "src"))
sys.path.insert(0, str(REMOTE_ROOT / "machine"))

from water_control.controller import Controller  # noqa: E402
from water_control.model import TelemetryQuality, TelemetrySample  # noqa: E402
from water_control.planner import GeneratedTablePlanner  # noqa: E402


def sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def envelope_to_sample(envelope: dict[str, Any]) -> TelemetrySample:
    required = {
        "sequence",
        "observed_at_s",
        "received_at_s",
        "tank_level_pct",
        "demand_lps",
        "power_available",
        "quality",
    }
    missing = sorted(required - envelope.keys())
    if missing:
        raise ValueError(f"missing envelope fields: {', '.join(missing)}")
    sequence = int(envelope["sequence"])
    if sequence <= 0:
        raise ValueError("sequence must be positive")
    return TelemetrySample(
        observed_at_s=int(envelope["observed_at_s"]),
        received_at_s=int(envelope["received_at_s"]),
        tank_level_pct=float(envelope["tank_level_pct"]),
        demand_lps=float(envelope["demand_lps"]),
        power_available=bool(envelope["power_available"]),
        quality=TelemetryQuality(str(envelope["quality"])),
    )


def main() -> int:
    edge_summary_path = (
        REPOSITORY_ROOT
        / "case-studies"
        / "edgestream"
        / "evidence"
        / "results"
        / "study-summary.json"
    )
    water_summary_path = REMOTE_ROOT / "evidence" / "results" / "study-summary.json"
    edge_summary = load(edge_summary_path)
    water_summary = load(water_summary_path)

    boundary_checks = {
        "edgestream_development_pass": edge_summary.get("status") == "PASS",
        "remote_water_development_pass": water_summary.get("development_result") == "PASS",
        "separate_evidence_roots": edge_summary_path.parent.resolve()
        != water_summary_path.parent.resolve(),
        "separate_component_identities": edge_summary.get("target")
        != water_summary.get("study_id"),
        "remote_formal_status_not_promoted": water_summary.get("formal_mncs_status") == "UNKNOWN",
    }

    envelopes = [
        {
            "sequence": 1,
            "observed_at_s": 0,
            "received_at_s": 0,
            "tank_level_pct": 48.0,
            "demand_lps": 3.8,
            "power_available": True,
            "quality": "GOOD",
        },
        {
            "sequence": 2,
            "observed_at_s": 0,
            "received_at_s": 240,
            "tank_level_pct": 48.0,
            "demand_lps": 3.8,
            "power_available": True,
            "quality": "STALE",
        },
        {
            "sequence": 3,
            "observed_at_s": 300,
            "received_at_s": 300,
            "tank_level_pct": 92.0,
            "demand_lps": 2.0,
            "power_available": True,
            "quality": "GOOD",
        },
    ]

    controller = Controller(GeneratedTablePlanner())
    intents = []
    for envelope in envelopes:
        sample = envelope_to_sample(envelope)
        intents.append(controller.decide(sample, sample.received_at_s).as_dict())

    behavior_checks = {
        "sequence_monotonic": [item["sequence"] for item in intents] == [1, 2, 3],
        "stale_envelope_degraded": intents[1]["mode"] in {"DEGRADED", "HOLD"},
        "high_high_disables_pumps": not intents[2]["duty_on"] and not intents[2]["standby_on"],
        "journal_valid": controller.journal.verify(),
    }

    status = "PASS" if all(boundary_checks.values()) and all(behavior_checks.values()) else "FAIL"
    summary = {
        "schema_version": "0.1",
        "study_id": "mncs.edgestream-remote-water.integration.development-1",
        "status": status,
        "formal_mncs_status": "UNKNOWN",
        "formal_mncds_status": "UNKNOWN",
        "boundary_checks": boundary_checks,
        "behavior_checks": behavior_checks,
        "intervention_counts": controller.intervention_counts,
        "identities": {
            "edgestream_summary": sha256(edge_summary_path),
            "remote_water_summary": sha256(water_summary_path),
            "adapter": sha256(Path(__file__)),
        },
        "limitations": [
            "This study consumes a normalized EdgeStream-shaped envelope, not a live EdgeStream process.",
            "Component claims and evidence roots remain separate and are not promoted by this result.",
            "No protected holdout, independent evaluator, industrial protocol, or actuator is in scope.",
        ],
    }
    output = ROOT / "evidence" / "results"
    output.mkdir(parents=True, exist_ok=True)
    (output / "integration-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
