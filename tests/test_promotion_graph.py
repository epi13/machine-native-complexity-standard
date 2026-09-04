# SPDX-License-Identifier: Apache-2.0

"""MNCS promotion graph subjects: multi-member evaluation without loops.

Graph mode lets one boundary evaluate evidence stamped for several exact
member revisions at once. The boundary must declare the same graph
(digest plus exact member set); anything else establishes no claim.
Repository-mode behavior is unchanged (see test_promotion_boundary.py).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "scripts/mncs_promotion_evaluate.py"

REPO_A = "epi13/mncs-actions"
REPO_B = "epi13/machine-native-complexity-development-specification"
COMMIT_A = "a" * 40
COMMIT_B = "b" * 40
DIGEST = "c" * 64

AUTHORITIES = {
    "mncs-validation": "machine-native-complexity-standard",
    "mncds-obligations": "machine-native-complexity-development-specification",
}


def _graph_doc(
    digest: str = DIGEST,
    members: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "mncs-actions.family-candidate-graph/1",
        "digest": digest,
        "members": members
        if members is not None
        else [
            {"repository": REPO_A, "commit": COMMIT_A},
            {"repository": REPO_B, "commit": COMMIT_B},
        ],
    }


def _boundary_doc(
    digest: str = DIGEST,
    members: list[dict[str, str]] | None = None,
    declare_graph: bool = True,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "schema_version": "mncs-promotion-boundary/0.1",
        "boundary_id": "family-advancement",
        "subject_repository": "mncs-family/graph",
        "required_evidence": [
            {
                "check_id": "mncs-validation",
                "authority": "machine-native-complexity-standard",
                "contract_revision": "0.2",
            },
            {
                "check_id": "mncds-obligations",
                "authority": "machine-native-complexity-development-specification",
                "contract_revision": "mncds-obligation-record/0.2",
            },
        ],
        "optional_evidence": [],
        "require_subject_binding": True,
        "obligation_check_id": "mncds-obligations",
        "tolerated_obligations": [],
        "extensions": {},
    }
    if declare_graph:
        doc["graph"] = {
            "digest": digest,
            "members": members
            if members is not None
            else [
                {"repository": REPO_A, "commit": COMMIT_A},
                {"repository": REPO_B, "commit": COMMIT_B},
            ],
        }
    return doc


def _check(
    check_id: str,
    repo: str,
    commit: str,
    verdict: str = "PASS",
    contract_revision: str | None = None,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "schema_version": "mncs.check-result/1",
        "id": check_id,
        "provider": f"provider-for-{check_id}",
        "verdict": verdict,
        "subject": {"repository": repo, "commit": commit},
    }
    if contract_revision is not None:
        doc["contract_revision"] = contract_revision
    return doc


def _obligation(key: str, repo: str, commit: str) -> dict[str, Any]:
    return {
        "schema_version": "mncds-obligation-record/0.2",
        "obligation_key": key,
        "status": "resolved",
        "required": True,
        "subject": {"repository": repo, "commit": commit},
        "origin": {"kind": "development-pressure", "authority": "mncs-actions"},
        "evidence": [],
        "supersedes": None,
        "extensions": {},
        "resolution": {
            "resolution": "fixed",
            "evidence_refs": ["sha256:" + "d" * 64],
            "resolved_by": repo,
            "resolved_at": "2026-09-04T00:00:00Z",
        },
    }


def _authority_map_doc() -> dict[str, Any]:
    return {
        "schema_version": "mncs-authority-map/0.1",
        "authorities": {
            check_id: {"provider": f"provider-for-{check_id}", "authority": authority}
            for check_id, authority in AUTHORITIES.items()
        },
    }


def _run(
    tmp_path: Path,
    *,
    graph: dict[str, Any] | None = None,
    boundary: dict[str, Any] | None = None,
    checks: list[dict[str, Any]] | None = None,
    obligations: list[dict[str, Any]] | None = None,
    extra_args: list[str] | None = None,
) -> tuple[int, dict[str, Any] | None]:
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(graph if graph is not None else _graph_doc()))
    boundary_path = tmp_path / "boundary.json"
    boundary_path.write_text(json.dumps(boundary if boundary is not None else _boundary_doc()))
    map_path = tmp_path / "authority-map.json"
    map_path.write_text(json.dumps(_authority_map_doc()))
    command = [
        sys.executable,
        str(EVALUATOR),
        "--boundary",
        str(boundary_path),
        "--authority-map",
        str(map_path),
        "--check-id",
        "promotion-boundary",
        "--output",
        str(tmp_path / "promotion.json"),
    ]
    if extra_args is not None:
        command.extend(extra_args)
    else:
        command.extend(["--subject-graph", str(graph_path)])
    check_paths = []
    for index, check in enumerate(
        checks
        if checks is not None
        else [
            _check("mncs-validation", REPO_A, COMMIT_A, contract_revision="0.2"),
            _check(
                "mncds-obligations",
                REPO_B,
                COMMIT_B,
                contract_revision="mncds-obligation-record/0.2",
            ),
        ]
    ):
        path = tmp_path / f"check-{index}.json"
        path.write_text(json.dumps(check))
        check_paths.append(str(path))
    command.extend(["--checks", *check_paths])
    for index, record in enumerate(
        obligations
        if obligations is not None
        else [_obligation("pressure.graph.a", REPO_A, COMMIT_A)]
    ):
        path = tmp_path / f"obligation-{index}.json"
        path.write_text(json.dumps(record))
        command.extend(["--obligations", str(path)])
    proc = subprocess.run(command, capture_output=True, text=True, timeout=60)
    out = tmp_path / "promotion.json"
    result = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else None
    return proc.returncode, result


def test_graph_pass_universe_binds_graph_subject(tmp_path: Path) -> None:
    code, result = _run(tmp_path)
    assert code == 0
    assert result is not None and result["verdict"] == "PASS"
    assert result["subject"] == {
        "repository": "mncs-family/graph",
        "commit": f"graph:{DIGEST}",
    }
    assert result["promotion"]["graph_digest"] == DIGEST
    assert result["promotion"]["required_total"] == 2


def test_evidence_from_outside_graph_is_no_claim(tmp_path: Path) -> None:
    code, result = _run(
        tmp_path,
        checks=[
            _check("mncs-validation", REPO_A, "d" * 40, contract_revision="0.2"),
            _check(
                "mncds-obligations",
                REPO_B,
                COMMIT_B,
                contract_revision="mncds-obligation-record/0.2",
            ),
        ],
    )
    assert code == 2
    assert result is None


def test_obligation_from_outside_graph_is_no_claim(tmp_path: Path) -> None:
    code, result = _run(tmp_path, obligations=[_obligation("pressure.graph.x", REPO_A, "d" * 40)])
    assert code == 2
    assert result is None


def test_digest_mismatch_is_no_claim(tmp_path: Path) -> None:
    code, result = _run(tmp_path, graph=_graph_doc(digest="e" * 64))
    assert code == 2
    assert result is None


def test_member_set_mismatch_is_no_claim(tmp_path: Path) -> None:
    code, result = _run(
        tmp_path,
        graph=_graph_doc(
            members=[{"repository": REPO_A, "commit": COMMIT_A}],
        ),
    )
    assert code == 2
    assert result is None


def test_boundary_without_graph_declaration_is_no_claim(tmp_path: Path) -> None:
    code, result = _run(tmp_path, boundary=_boundary_doc(declare_graph=False))
    assert code == 2
    assert result is None


def test_graph_subject_with_repository_subject_is_no_claim(tmp_path: Path) -> None:
    code, result = _run(
        tmp_path,
        extra_args=[
            "--subject-graph",
            str(tmp_path / "graph.json"),
            "--subject-repository",
            REPO_A,
            "--subject-commit",
            COMMIT_A,
        ],
    )
    assert code == 2
    assert result is None


def test_moving_ref_member_is_no_claim(tmp_path: Path) -> None:
    code, result = _run(
        tmp_path,
        graph=_graph_doc(
            members=[
                {"repository": REPO_A, "commit": "main"},
                {"repository": REPO_B, "commit": COMMIT_B},
            ]
        ),
    )
    assert code == 2
    assert result is None


def test_duplicate_members_are_no_claim(tmp_path: Path) -> None:
    code, result = _run(
        tmp_path,
        graph=_graph_doc(
            members=[
                {"repository": REPO_A, "commit": COMMIT_A},
                {"repository": REPO_A, "commit": COMMIT_A},
            ]
        ),
    )
    assert code == 2
    assert result is None


def test_wrong_graph_namespace_is_no_claim(tmp_path: Path) -> None:
    boundary = _boundary_doc()
    boundary["subject_repository"] = REPO_A
    code, result = _run(tmp_path, boundary=boundary)
    assert code == 2
    assert result is None


def test_open_member_obligation_blocks_graph(tmp_path: Path) -> None:
    record = _obligation("pressure.graph.open", REPO_B, COMMIT_B)
    record["status"] = "open"
    del record["resolution"]
    code, result = _run(tmp_path, obligations=[record])
    assert code == 0
    assert result is not None and result["verdict"] == "UNKNOWN"
    assert any("pressure.graph.open" in item for item in result["promotion"]["blockers"])
