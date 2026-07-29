from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rust_consumer_agrees_with_entire_release_candidate_corpus() -> None:
    process = subprocess.run(
        [
            "cargo",
            "run",
            "--quiet",
            "--manifest-path",
            "independent/rc-consumer/Cargo.toml",
            "--",
            "conformance/release-candidate/corpus.json",
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["summary"]["agreement"] == 72
    assert result["summary"]["disagreement"] == 0
    assert result["summary"]["unsupported"] == 0
    assert result["operator_independence"] == "UNKNOWN"
    assert result["organizational_independence"] == "UNKNOWN"
