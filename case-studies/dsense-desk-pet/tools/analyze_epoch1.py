#!/usr/bin/env python3
"""Reproduce the dSense epoch-1 telemetry analysis with the Python standard library."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import statistics
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_NAME = "epoch-1-reactivity.csv.zlib.b85"
DEFAULT_OUTPUT = ROOT / "evidence" / "results" / "epoch-1-analysis.json"


def decode_artifact(name: str) -> bytes:
    parts = sorted((ROOT / "artifacts").glob(f"{name}.part*"))
    if not parts:
        raise ValueError(f"no artifact parts found for {name}")
    encoded = "".join(
        token
        for part in parts
        for token in part.read_text(encoding="ascii").split()
    )
    return zlib.decompress(base64.b85decode(encoded.encode("ascii")))


def parse_number(value: str) -> int | float | str:
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def load_capture(data: bytes) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    headers: dict[str, list[str]] = {}
    records: dict[str, list[dict[str, Any]]] = {"D": [], "P": [], "E": []}
    markers: list[dict[str, Any]] = []

    for raw_line in data.decode("utf-8").splitlines():
        if not raw_line:
            continue
        if raw_line.startswith(("#D,", "#P,", "#E,")):
            row = next(csv.reader([raw_line[1:]]))
            headers[row[0]] = row[1:]
            continue
        if raw_line.startswith("#MARK,"):
            row = next(csv.reader([raw_line[1:]]))
            markers.append(
                {
                    "host_iso": row[1],
                    "host_elapsed_seconds": float(row[2]),
                    "label": row[3],
                }
            )
            continue
        if len(raw_line) < 2 or raw_line[0] not in records or raw_line[1] != ",":
            continue

        row = next(csv.reader([raw_line]))
        kind = row[0]
        fields = headers.get(kind)
        if fields is None or len(fields) != len(row) - 1:
            raise ValueError(f"Malformed {kind} record with {len(row) - 1} fields")
        records[kind].append(
            {name: parse_number(value) for name, value in zip(fields, row[1:], strict=True)}
        )

    if not records["D"] or not records["E"] or not records["P"]:
        raise ValueError("Capture is missing one or more required D/P/E record classes")
    return records, markers


def mean(rows: list[dict[str, Any]], field: str) -> float:
    return statistics.fmean(float(row[field]) for row in rows)


def build_summary(data: bytes) -> dict[str, Any]:
    records, markers = load_capture(data)
    snapshots = records["D"]
    events = records["E"]
    start_ms = int(snapshots[0]["ms"])
    end_ms = int(snapshots[-1]["ms"])
    duration_seconds = (end_ms - start_ms) / 1000.0
    acoustic_events = [row for row in events if int(row["code"]) == 1]
    counter_delta = int(snapshots[-1]["events"]) - int(snapshots[0]["events"])

    segments: list[dict[str, Any]] = []
    for index, marker in enumerate(markers):
        segment_start = marker["host_elapsed_seconds"] * 1000.0
        segment_end = (
            markers[index + 1]["host_elapsed_seconds"] * 1000.0
            if index + 1 < len(markers)
            else float(end_ms)
        )
        segment_data = [
            row for row in snapshots if segment_start <= float(row["ms"]) < segment_end
        ]
        segment_events = [
            row for row in acoustic_events if segment_start <= float(row["ms"]) < segment_end
        ]
        if not segment_data or segment_end <= segment_start:
            continue
        seconds = (segment_end - segment_start) / 1000.0
        segments.append(
            {
                "label": marker["label"],
                "duration_seconds": round(seconds, 3),
                "acoustic_events": len(segment_events),
                "event_rate_hz": round(len(segment_events) / seconds, 6),
                "mic_envelope_mean": round(mean(segment_data, "mic_env"), 6),
                "mic_envelope_max": max(int(row["mic_env"]) for row in segment_data),
                "external_energy_mean": round(mean(segment_data, "mic_ext"), 6),
                "novelty_mean": round(mean(segment_data, "novelty"), 6),
            }
        )

    novelty_values = [int(row["novelty"]) for row in snapshots]
    noise_floor_values = [int(row["mic_nf"]) for row in snapshots]
    envelope_values = [int(row["mic_env"]) for row in snapshots]

    return {
        "schema_version": "1.0",
        "study_id": "dsense.desk-pet.calibration.epoch-1",
        "source": {
            "path": "artifacts/epoch-1-reactivity.csv.zlib.b85",
            "decoded_sha256": hashlib.sha256(data).hexdigest(),
            "encoding": "zlib+base85 text envelope",
            "telemetry_protocol": "DSENSE_TELEMETRY_V1",
        },
        "capture": {
            "device_ms_start": start_ms,
            "device_ms_end": end_ms,
            "duration_seconds": round(duration_seconds, 3),
            "record_counts": {
                "data": len(records["D"]),
                "model": len(records["P"]),
                "events": len(records["E"]),
                "markers": len(markers),
            },
        },
        "observations": {
            "acoustic_event_records": len(acoustic_events),
            "acoustic_counter_delta": counter_delta,
            "acoustic_event_rate_hz": round(counter_delta / duration_seconds, 6),
            "microphone_envelope": {
                "minimum": min(envelope_values),
                "maximum": max(envelope_values),
                "mean": round(statistics.fmean(envelope_values), 6),
                "median": statistics.median(envelope_values),
            },
            "learned_noise_floor": {
                "minimum": min(noise_floor_values),
                "maximum": max(noise_floor_values),
                "mean": round(statistics.fmean(noise_floor_values), 6),
                "median": statistics.median(noise_floor_values),
            },
            "novelty": {
                "minimum": min(novelty_values),
                "maximum": max(novelty_values),
                "mean": round(statistics.fmean(novelty_values), 6),
                "fraction_at_or_above_1000": round(
                    sum(value >= 1000 for value in novelty_values) / len(novelty_values), 9
                ),
            },
            "segments": segments,
        },
        "derived_findings": [
            (
                "The acoustic detector retriggered at approximately its refractory limit "
                "across quiet, voice, desk-tap, and direct-contact segments."
            ),
            (
                "The learned microphone noise floor remained fixed at four ADC-deviation "
                "units while the observed envelope stayed between 187 and 592."
            ),
            (
                "Novelty was at or above 1000 for more than 99 percent of operating "
                "snapshots, so acoustic activity had saturated the cognitive signal."
            ),
            (
                "Direct piezo contact was measurably stronger than the quiet baseline, "
                "showing usable dynamic range even though event classification failed."
            ),
            (
                "The light-cover segment coincided with a persistent microphone rise, "
                "motivating ADC multiplexer settling and cross-channel isolation."
            ),
        ],
        "result": {
            "development_status": "FAIL",
            "reason": (
                "The epoch-1 detector did not distinguish quiet periods from intentional "
                "acoustic or mechanical stimuli."
            ),
            "formal_mncs_status": "UNKNOWN",
            "formal_mncds_status": "UNKNOWN",
            "promotion_authorized": False,
        },
    }


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    data = args.input.read_bytes() if args.input else decode_artifact(DEFAULT_ARTIFACT_NAME)
    rendered = canonical_json(build_summary(data))
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            print(f"Evidence mismatch: regenerate {args.output}")
            return 1
        print("epoch-1 telemetry evidence matches the checked-in result")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
