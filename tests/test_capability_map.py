# SPDX-License-Identifier: Apache-2.0

"""Owner capability map for family pin coherence.

The map classifies MNCS tree paths so the family orchestrator can decide
whether a downstream pin must advance when MNCS moves. Unmapped paths fail
closed to UNKNOWN and block automatic advancement, so this test locks two
properties: the map shape the orchestrator consumes, and full coverage of
the tracked tree (skipped outside a git checkout).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "promotion" / "capability-map.json"
SLUG = "epi13/machine-native-complexity-standard"
IMPACTS = {"executable", "contract", "evidence", "docs", "none"}


def _load() -> dict:
    return json.loads(MAP.read_text(encoding="utf-8"))


def test_capability_map_shape():
    doc = _load()
    rows = doc["capabilities"][SLUG]
    assert isinstance(rows, list) and rows
    for row in rows:
        assert row["paths"], f"row has no paths: {row}"
        assert all(isinstance(p, str) and p for p in row["paths"])
        assert row["impact"] in IMPACTS, f"unknown impact: {row['impact']}"


def test_capability_map_covers_tracked_tree():
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0:
        import pytest

        pytest.skip("not a git checkout")
    rows = _load()["capabilities"][SLUG]
    prefixes = [prefix for row in rows for prefix in row["paths"]]
    unmapped = [
        path
        for path in proc.stdout.splitlines()
        if not any(path == prefix or path.startswith(prefix) for prefix in prefixes)
    ]
    assert unmapped == []
