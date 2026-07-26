# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest

from mncs_validator.validation import validate_bundle

ROOT = Path(__file__).resolve().parents[1]
BUNDLES = [
    "minimal",
    "http-chunked-decoder",
    "rejected-candidate",
    "repair-workflow",
    "structural-provider",
]


@pytest.mark.parametrize("name", BUNDLES)
def test_example_bundle(name: str) -> None:
    report = validate_bundle(ROOT / "examples" / name)
    assert report.valid, report.as_dict()


def test_rejected_candidate_is_validly_rejected() -> None:
    report = validate_bundle(ROOT / "examples/rejected-candidate")
    assert report.valid
    assert report.declared_status == "FAIL"
    assert report.computed_status == "FAIL"


def test_no_example_requires_network(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", blocked)
    for name in BUNDLES:
        assert validate_bundle(ROOT / "examples" / name).valid
