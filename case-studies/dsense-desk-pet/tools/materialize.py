#!/usr/bin/env python3
"""Restore byte-identical dSense machine artifacts from compact text envelopes."""

from __future__ import annotations

import argparse
import base64
import hashlib
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
DEFAULT_OUTPUT = ROOT / ".materialized"

BASELINE_NAME = "DeskPet_dSense_Interface_Telemetry_MNCS.ino"
TELEMETRY_NAME = "DeskPet_dSense_UnoMax_Binary_MNCS.ino"
PRODUCTION_NAME = "DeskPet_dSense_UnoMax_MNCS.ino"
RAW_NAME = "epoch-1-reactivity.csv"

EXPECTED_SHA256 = {
    BASELINE_NAME: "3b55e368310f957d55588bd82afcbc905043e302634ef44ce478f2ced57abaca",
    TELEMETRY_NAME: "8c413fb12cc5ff3333175ff20ff5093b7cf98d297983b1472aa71ece53411808",
    PRODUCTION_NAME: "bcaa5bb03a3d7b86001d45f7890003f6d82a8e982ebdc38163a84baa460fa74e",
    RAW_NAME: "01c76dca4582673df89d8834d109a1cad6c984d0a5c493063ed8ff526ff74eb3",
}


def decode_text_artifact(name: str) -> bytes:
    parts = sorted(ARTIFACTS.glob(f"{name}.part*"))
    if not parts:
        raise ValueError(f"no artifact parts found for {name}")
    encoded = "".join(
        token
        for part in parts
        for token in part.read_text(encoding="ascii").split()
    )
    return zlib.decompress(base64.b85decode(encoded.encode("ascii")))


def production_from_telemetry(source: bytes) -> bytes:
    before = b"constexpr bool DEBUG_SERIAL = true;"
    after = b"constexpr bool DEBUG_SERIAL = false;"
    if source.count(before) != 1:
        raise ValueError("telemetry source does not contain one DEBUG_SERIAL=true declaration")
    return source.replace(before, after, 1)


def materialized_artifacts() -> dict[str, bytes]:
    telemetry = decode_text_artifact("firmware-v5-telemetry.ino.zlib.b85")
    return {
        BASELINE_NAME: decode_text_artifact("baseline-v4.ino.zlib.b85"),
        TELEMETRY_NAME: telemetry,
        PRODUCTION_NAME: production_from_telemetry(telemetry),
        RAW_NAME: decode_text_artifact("epoch-1-reactivity.csv.zlib.b85"),
    }


def verify_identity(name: str, content: bytes) -> None:
    actual = hashlib.sha256(content).hexdigest()
    expected = EXPECTED_SHA256[name]
    if actual != expected:
        raise ValueError(f"identity mismatch for {name}: {actual} != {expected}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    artifacts = materialized_artifacts()
    for name, content in artifacts.items():
        verify_identity(name, content)

    if args.check:
        print("materialized artifact identities match")
        return 0

    args.output.mkdir(parents=True, exist_ok=True)
    for name, content in artifacts.items():
        destination = args.output / name
        destination.write_bytes(content)
        print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
