#!/usr/bin/env python3
"""Fast deterministic EdgeStream smoke test for normal CI."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, cwd=ROOT, check=True, capture_output=True)


def main() -> int:
    run([sys.executable, "tools/run_study.py", "generate"])
    run([sys.executable, "tools/run_study.py", "build"])
    source = ROOT / "machine" / "edgestream_generated.c"
    first = hashlib.sha256(source.read_bytes()).digest()
    with tempfile.TemporaryDirectory() as directory:
        other = Path(directory) / "generated.c"
        run(
            [
                sys.executable,
                "generator/generate_candidate.py",
                "--reference",
                "reference/edgestream_reference.c",
                "--output",
                str(other),
            ]
        )
        second = hashlib.sha256(other.read_bytes()).digest()
    if first != second:
        raise SystemExit("candidate regeneration is not byte-identical")

    workload = ROOT / "workloads" / "edge-cases.bin"
    reference = ROOT / "build" / "reference-gcc"
    candidate = ROOT / "build" / "candidate-gcc"
    if not reference.exists():
        reference = ROOT / "build" / "reference-clang"
        candidate = ROOT / "build" / "candidate-clang"
    ref = run([str(reference), "--chunk", "3", str(workload)])
    machine = run([str(candidate), "--chunk", "31", str(workload)])
    if ref.stdout != machine.stdout:
        raise SystemExit("reference and candidate smoke outputs differ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
