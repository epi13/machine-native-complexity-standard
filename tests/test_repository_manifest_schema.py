from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "schemas/mncs-family-repository-manifest-v0alpha1.schema.json").read_text()
)


def test_repository_layout_extension_is_valid_and_bounded() -> None:
    manifest = {
        "schema_version": "mncs-family.repository-manifest/v0alpha1",
        "repository": "fixture-repository",
        "revision": 1,
        "contracts": {"provides": [], "consumes": [], "tests": []},
        "organization": {
            "layout": "mncs.repository-layout/1",
            "surfaces": [
                {
                    "path": "native/mncs/core.mncs",
                    "class": "canonical",
                    "authority": "fixture-repository",
                },
                {
                    "path": "tools/reference.py",
                    "class": "differential-oracle",
                },
            ],
            "generated_regions": [
                {
                    "path": "README.md",
                    "begin": "<!-- MNCS:generated:begin -->",
                    "end": "<!-- MNCS:generated:end -->",
                    "source": "mncs.family-agent-context/1",
                }
            ],
        },
    }
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(manifest), key=str)
    assert errors == []


def test_unknown_artifact_class_is_rejected() -> None:
    manifest = {
        "schema_version": "mncs-family.repository-manifest/v0alpha1",
        "repository": "fixture-repository",
        "revision": 1,
        "contracts": {"provides": [], "consumes": [], "tests": []},
        "organization": {
            "layout": "mncs.repository-layout/1",
            "surfaces": [{"path": "src", "class": "semantic-authority"}],
        },
    }
    errors = list(Draft202012Validator(SCHEMA).iter_errors(manifest))
    assert errors


def test_orthogonal_surface_classification_distinguishes_bootstrap_and_semantics() -> None:
    manifest = {
        "schema_version": "mncs-family.repository-manifest/v0alpha1",
        "repository": "fixture-repository",
        "revision": 1,
        "contracts": {"provides": [], "consumes": [], "tests": []},
        "organization": {
            "layout": "mncs.repository-layout/1",
            "surfaces": [
                {
                    "path": "crates/",
                    "class": "canonical",
                    "classification": {
                        "authority": "canonical",
                        "lifecycle": "active",
                        "boundary_kind": "compiler-bootstrap",
                        "semantic_role": "canonical-semantic",
                    },
                },
                {
                    "path": "tools/legacy.py",
                    "class": "migration-shadow",
                    "classification": {
                        "authority": "none",
                        "lifecycle": "temporary",
                        "boundary_kind": "filesystem",
                        "semantic_role": "temporary-host-semantic",
                    },
                },
                {
                    "path": "src/semantic.py",
                    "class": "canonical",
                    "classification": {
                        "authority": "canonical",
                        "lifecycle": "temporary",
                        "boundary_kind": "process",
                        "semantic_role": "canonical-host-semantic",
                    },
                },
            ],
        },
    }
    assert list(Draft202012Validator(SCHEMA).iter_errors(manifest)) == []


def test_manifest_points_to_a_bounded_verification_inventory() -> None:
    manifest = {
        "schema_version": "mncs-family.repository-manifest/v0alpha1",
        "repository": "fixture-repository",
        "revision": 2,
        "contracts": {"provides": [], "consumes": [], "tests": []},
        "verification": {
            "schema_version": "mncs-family.verification-obligation-inventory/v1",
            "obligation_inventory": ".mncs/verification-obligations.json",
        },
    }
    assert list(Draft202012Validator(SCHEMA).iter_errors(manifest)) == []


def test_cargo_target_expansion_is_an_explicit_bounded_command_mode() -> None:
    base = {
        "schema_version": "mncs-family.repository-manifest/v0alpha1",
        "repository": "fixture-repository",
        "revision": 2,
        "contracts": {
            "provides": [{
                "contract": "compiler",
                "version": "1",
                "kind": "compiler",
                "stability": "stable",
            }],
            "consumes": [],
            "tests": [],
        },
        "verification": {
            "schema_version": "mncs-family.verification-obligation-inventory/v1",
            "obligation_inventory": ".mncs/verification-obligations.json",
        },
    }
    valid = {
        **base,
        "contracts": {
            **base["contracts"],
            "tests": [{
                "test": "bounded-cargo-tests",
                "covers": ["compiler"],
                "invalidation_dependencies": ["examples/"],
                "obligation": "self",
                "command": {
                    "argv": ["cargo", "test", "--package", "fixture"],
                    "timeout_seconds": 600,
                    "target_mode": "cargo_test_targets",
                },
            }],
        },
    }
    invalid = {
        **valid,
        "contracts": {
            **valid["contracts"],
            "tests": [{
                **valid["contracts"]["tests"][0],
                "command": {
                    **valid["contracts"]["tests"][0]["command"],
                    "target_mode": "all_tests",
                },
            }],
        },
    }
    assert list(Draft202012Validator(SCHEMA).iter_errors(valid)) == []
    assert list(Draft202012Validator(SCHEMA).iter_errors(invalid))


def test_verification_inventory_uses_orthogonal_dimensions() -> None:
    inventory_schema = json.loads(
        (ROOT / "schemas/mncs-family-verification-obligation-inventory-v1.schema.json").read_text()
    )
    inventory = {
        "schema_version": "mncs-family.verification-obligation-inventory/v1",
        "repository": "fixture-repository",
        "revision": 1,
        "obligations": [
            {
                "identity": "fixture.obligation.native-regression",
                "guarantee_domain": "semantic",
                "evidence_role": "canonical_regression",
                "lifecycle": "permanent",
                "scope": "local",
                "subjects": ["fixture:subject"],
                "invalidation_dependencies": ["fixture.contract/1"],
                "executor": {
                    "provider": "fixture-repository",
                    "kind": "native_first_class_test",
                    "entrypoint": "mncs-test",
                    "declaration_identities": ["fixture:test-declaration"],
                },
                "evidence_identity": {
                    "subject_fields": ["subject_fingerprint"],
                    "definition_fields": ["obligation_identity"],
                    "execution_fields": ["test_case_identity", "verifier_identity"],
                },
            }
        ],
    }
    assert list(Draft202012Validator(inventory_schema).iter_errors(inventory)) == []
