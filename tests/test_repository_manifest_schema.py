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
