# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_conformance_corpus_runner_is_deterministic() -> None:
    command = [sys.executable, str(ROOT / "scripts/run-conformance-corpus")]
    first = subprocess.run(command, check=True, capture_output=True, text=True)
    second = subprocess.run(command, check=True, capture_output=True, text=True)
    assert first.stdout == second.stdout
    result = json.loads(first.stdout)
    assert result["mismatch_count"] == 0
    assert result["case_count"] >= 28
