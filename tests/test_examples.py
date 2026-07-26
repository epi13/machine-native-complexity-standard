# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest

from mncs_validator.validation import validate_bundle

ROOT = Path(__file__).resolve().parents[1]
PASS_BUNDLES = [
    "minimal",
    "http-chunked-decoder",
    "repair-workflow",
    "structural-provider",
    "validator-rule-engine",
]
ALL_BUNDLES = [*PASS_BUNDLES, "rejected-candidate", "legacy-0.1"]


@pytest.mark.parametrize("name", ALL_BUNDLES)
def test_example_bundle(name: str) -> None:
    report = validate_bundle(ROOT / "examples" / name)
    assert report.valid, report.as_dict()


@pytest.mark.parametrize("name", PASS_BUNDLES)
def test_primary_pass_examples_are_certifiable(name: str) -> None:
    report = validate_bundle(ROOT / "examples" / name)
    assert report.certification_eligible, report.as_dict()


def test_rejected_candidate_is_validly_rejected() -> None:
    report = validate_bundle(ROOT / "examples/rejected-candidate")
    assert report.valid
    assert report.declared_status == "FAIL"
    assert report.computed_status == "FAIL"
    assert not report.certification_eligible


def test_legacy_example_is_reduced_assurance() -> None:
    report = validate_bundle(ROOT / "examples/legacy-0.1")
    assert report.valid
    assert report.legacy_self_asserted_acceptance
    assert report.reduced_assurance
    assert not report.certification_eligible
    override = validate_bundle(ROOT / "examples/legacy-0.1", allow_legacy=True)
    assert override.certification_eligible
    assert override.legacy_override_used


def test_no_example_requires_network(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", blocked)
    for name in ALL_BUNDLES:
        assert validate_bundle(ROOT / "examples" / name).valid
