# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

from mncs_validator.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_version(capsys: object) -> None:
    assert main(["version"]) == 0


def test_validate_json_output(capsys: object) -> None:
    assert main(["validate", str(ROOT / "examples/minimal/manifest.json"), "--json"]) == 0
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    value = json.loads(captured.out)
    assert value["valid"] is True
    assert value["computed_status"] == "PASS"


def test_invalid_cli_exit_code(capsys: object) -> None:
    path = ROOT / "tests/fixtures/invalid-manifest.json"
    assert main(["validate", str(path)]) == 1


def test_schema_lookup_json(capsys: object) -> None:
    assert main(["schema", "manifest", "--json"]) == 0
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert json.loads(captured.out)["title"] == "MNCS conformance manifest"


def test_hash_and_summarize(capsys: object) -> None:
    assert main(["hash", str(ROOT / "NOTICE"), "--json"]) == 0
    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert json.loads(captured.out)["sha256"].startswith("sha256:")
    assert main(["summarize", str(ROOT / "examples/minimal/manifest.json")]) == 0


def test_init_refuses_nonempty_directory(tmp_path: Path) -> None:
    target = tmp_path / "bundle"
    target.mkdir()
    (target / "existing").write_text("preserve")
    assert main(["init", str(target)]) == 2
    assert (target / "existing").read_text() == "preserve"
