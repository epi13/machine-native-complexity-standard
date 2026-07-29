from __future__ import annotations

import json
from pathlib import Path

from mncs_validator.assurance import validate_rc_value
from mncs_validator.mncds import validate_development_value
from mncs_validator.rc_corpus import load_cases, run_corpus

ROOT = Path(__file__).resolve().parents[1]


def test_release_candidate_examples() -> None:
    for kind, relative in (
        ("contract", "examples/release-candidate-0.3/contract-profile.json"),
        ("assurance", "examples/release-candidate-0.3/assurance-case.json"),
        ("threat", "examples/release-candidate-0.3/threat-record.json"),
        ("measurement", "examples/release-candidate-0.3/measurement-profile.json"),
    ):
        value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        report = validate_rc_value(value, kind)  # type: ignore[arg-type]
        assert report.valid
        assert report.category == "PASS"


def test_mncds_release_candidate_truthfully_retains_external_unknown() -> None:
    path = ROOT / "examples/mncds-0.1-rc/development-record.json"
    report = validate_development_value(json.loads(path.read_text(encoding="utf-8")))
    assert report.valid
    assert report.category == "UNKNOWN"
    assert {warning.code for warning in report.warnings} == {"protected-evidence-unknown"}


def test_release_candidate_corpus_has_no_mismatches() -> None:
    summary, results = run_corpus(ROOT / "conformance/release-candidate/corpus.json")
    assert summary.total >= 50
    assert summary.mismatched == 0, [result for result in results if not result["matched"]]
    assert {"PASS", "FAIL", "UNKNOWN", "INVALID", "UNSUPPORTED"} <= set(summary.categories)


def test_named_release_candidate_suites_resolve_and_cover_required_categories() -> None:
    corpus_path = ROOT / "conformance/release-candidate/corpus.json"
    _, cases = load_cases(corpus_path)
    _, results = run_corpus(corpus_path)
    actual = {result["id"]: result["actual"] for result in results}
    identifiers = {case["id"] for case in cases}
    index = json.loads(
        (ROOT / "conformance/release-candidate/suite-index.json").read_text(encoding="utf-8")
    )
    for suite in index["suites"]:
        selection = suite["selection"]
        selected = (
            {
                identifier
                for identifier in identifiers
                if identifier.startswith(selection["id_prefix"])
            }
            if "id_prefix" in selection
            else set(selection["ids"])
        )
        assert selected
        assert selected <= identifiers
        assert set(suite["required_categories"]) <= {actual[identifier] for identifier in selected}


def test_rc_schema_sources_match_packaged_resources() -> None:
    filenames = [
        "mncs-contract-profile-0.3.schema.json",
        "mncs-assurance-case-0.3.schema.json",
        "mncs-threat-record-0.3.schema.json",
        "mncs-measurement-profile-0.3.schema.json",
        "mncds-development-record-0.1.schema.json",
    ]
    for filename in filenames:
        source = ROOT / "schemas" / filename
        packaged = ROOT / "src/mncs_validator/resources/schemas" / filename
        assert source.read_bytes() == packaged.read_bytes()
        assert json.loads(source.read_text(encoding="utf-8"))["additionalProperties"] is False


def test_gap_matrix_has_no_unfinished_local_release_blocker() -> None:
    matrix = json.loads((ROOT / "docs/release-gap-matrix.json").read_text(encoding="utf-8"))
    required_fields = {
        "requirement_id",
        "origin",
        "normative_strength",
        "implementation_status",
        "schema_status",
        "python_validation_status",
        "independent_consumer_status",
        "positive_fixture_status",
        "negative_fixture_status",
        "interoperability_status",
        "documentation_status",
        "migration_status",
        "security_review_status",
        "governance_status",
        "evidence_identity",
        "blocking_issues",
        "gap_class",
        "locally_executable_remaining",
        "external_actor_required",
    }
    for requirement in matrix["requirements"]:
        assert required_fields <= set(requirement)
        assert requirement["locally_executable_remaining"] is False
