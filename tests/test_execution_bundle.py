# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import os
import stat
import zipfile
from pathlib import Path

import pytest

from mncs_validator.canonical import canonicalize
from mncs_validator.cli import main
from mncs_validator.execution_bundle import (
    MAX_FILE_BYTES,
    MAX_TOTAL_BYTES,
    bind_receipt_to_bundle,
    build_execution_bundle,
    normalize_bundle_path,
    verify_execution_bundle_archive,
)
from mncs_validator.schemas import load_schema, schema_errors

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "experimental/execution-bundle/fixtures/source"
SOURCE_MANIFEST = ROOT / "experimental/execution-bundle/fixtures/generic-source.json"


def _source(tmp_path: Path, **changes: object) -> tuple[Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    value = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    value.update(changes)
    path = tmp_path / "source.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path, SOURCE_ROOT


def _build(tmp_path: Path, *, source_manifest: Path = SOURCE_MANIFEST) -> tuple[Path, object]:
    archive = tmp_path / "bundle.zip"
    report = build_execution_bundle(source_manifest, SOURCE_ROOT, archive)
    assert report.valid, report.as_dict()
    return archive, report


def _zip(
    path: Path,
    members: list[tuple[str, bytes, int | None]],
    *,
    compression: int = zipfile.ZIP_STORED,
) -> None:
    with (
        path.open("wb") as stream,
        zipfile.ZipFile(stream, "w", compression=compression) as archive,
    ):
        for name, content, mode in members:
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = compression
            if mode is not None:
                info.create_system = 3
                info.external_attr = mode << 16
            archive.writestr(info, content)


def test_schema_is_packaged_and_reference_bundle_is_valid(tmp_path: Path) -> None:
    assert load_schema("execution-bundle")["title"].startswith("MNCS experimental")
    assert schema_errors(json.loads(SOURCE_MANIFEST.read_text()), "execution-bundle-source") == []
    archive, built = _build(tmp_path)
    verified = verify_execution_bundle_archive(archive)
    assert verified.valid
    assert verified.bundle_identity == built.bundle_identity
    assert verified.archive_identity == built.archive_identity
    assert verified.manifest is not None
    expected_manifest = json.loads(
        (ROOT / "experimental/execution-bundle/fixtures/valid/manifest.json").read_text()
    )
    assert verified.manifest == expected_manifest
    corpus = json.loads(
        (ROOT / "experimental/execution-bundle/fixtures/corpus-index.json").read_text()
    )
    assert len(corpus["cases"]) >= 40
    assert {case["expected"] for case in corpus["cases"]} >= {"PASS", "INVALID", "UNSUPPORTED"}


def test_deterministic_rebuild_has_identical_logical_and_transport_identity(tmp_path: Path) -> None:
    first, first_report = _build(tmp_path / "first")
    second, second_report = _build(tmp_path / "second")
    assert first_report.bundle_identity == second_report.bundle_identity
    assert first_report.manifest == second_report.manifest
    assert first_report.archive_identity == second_report.archive_identity
    assert first.read_bytes() == second.read_bytes()


def test_material_mutations_change_logical_identity(tmp_path: Path) -> None:
    base_archive, base = _build(tmp_path / "base")
    assert verify_execution_bundle_archive(base_archive).valid
    mutations = [
        {"bundle_id": "bundle.other-v1"},
        {"entrypoints": [{"name": "other", "path": "harness/run.py"}]},
        {"runtime_requirements": []},
        {"policy_references": []},
    ]
    for index, mutation in enumerate(mutations):
        source, root = _source(tmp_path / f"mutation-{index}", **mutation)
        archive = tmp_path / f"mutation-{index}" / "bundle.zip"
        report = build_execution_bundle(source, root, archive)
        assert report.valid, report.as_dict()
        assert report.bundle_identity != base.bundle_identity

    changed_root = tmp_path / "changed-content"
    changed_root.mkdir()
    for path in SOURCE_ROOT.rglob("*"):
        if path.is_file():
            target = changed_root / path.relative_to(SOURCE_ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    for relative in (
        "tests/test.py",
        "harness/run.py",
        "runtime/requirements.json",
        "policy/execution-policy.json",
    ):
        changed = changed_root / relative
        changed.write_bytes(changed.read_bytes() + b"\n")
        report = build_execution_bundle(
            SOURCE_MANIFEST, changed_root, tmp_path / f"changed-{relative.replace('/', '-')}.zip"
        )
        assert report.valid
        assert report.bundle_identity != base.bundle_identity
        changed.write_bytes(changed.read_bytes()[:-1])


def test_receipt_binding_is_exact_and_fail_closed(tmp_path: Path) -> None:
    archive, built = _build(tmp_path)
    manifest = built.manifest
    assert manifest is not None
    receipt = {
        "bundle": {
            "test_bundle_identity": built.bundle_identity,
            "harness_identity": manifest["harness_identity"],
            "input_snapshot_identity": manifest["input_snapshot_identity"],
        },
        "policy": {"execution_policy_identity": manifest["policy_identity"]},
    }
    assert bind_receipt_to_bundle(receipt, verify_execution_bundle_archive(archive)).valid
    stale = copy.deepcopy(receipt)
    stale["bundle"]["test_bundle_identity"] = "0" * 64
    assert not bind_receipt_to_bundle(stale, verify_execution_bundle_archive(archive)).valid
    changed_policy = copy.deepcopy(receipt)
    changed_policy["policy"]["execution_policy_identity"] = "1" * 64
    assert not bind_receipt_to_bundle(
        changed_policy, verify_execution_bundle_archive(archive)
    ).valid
    assert not verify_execution_bundle_archive(archive, expected_bundle_identity="2" * 64).valid
    assert not verify_execution_bundle_archive(
        archive, expected_archive_identity="sha256:" + "2" * 64
    ).valid


def test_bundle_cli_create_and_verify(tmp_path: Path, capsys: object) -> None:
    archive = tmp_path / "cli.zip"
    assert (
        main(
            [
                "bundle",
                "create",
                "--manifest",
                str(SOURCE_MANIFEST),
                "--source",
                str(SOURCE_ROOT),
                "--output",
                str(archive),
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()  # type: ignore[attr-defined]
    assert main(["bundle", "verify", str(archive), "--json"]) == 0
    result = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert result["category"] == "PASS"


@pytest.mark.parametrize(
    "path",
    [
        "../escape",
        "/absolute",
        "C:/drive",
        "C:\\drive",
        "\\\\server\\share",
        "./dot",
        "a//b",
        "a/../b",
        "a\x00b",
        "manifest.json",
        "e\u0301.txt",
    ],
)
def test_portable_path_normalization_rejects_ambiguous_paths(path: str) -> None:
    with pytest.raises(ValueError):
        normalize_bundle_path(path)


def test_builder_rejects_case_collision_and_links(tmp_path: Path) -> None:
    source, root = _source(
        tmp_path,
        entries=[
            {"path": "tests/Test.py", "source": "tests/test.py", "role": "test", "mode": "0644"},
            {"path": "tests/test.py", "source": "tests/test.py", "role": "support", "mode": "0644"},
        ],
        entrypoints=[{"name": "test", "path": "tests/test.py"}],
        runtime_requirements=[],
        policy_references=[],
    )
    report = build_execution_bundle(source, root, tmp_path / "collision.zip")
    assert not report.valid
    assert any(issue.code == "CASE-COLLISION" for issue in report.issues)

    link_root = tmp_path / "links"
    link_root.mkdir()
    (link_root / "real.txt").write_text("x", encoding="utf-8")
    os.symlink(link_root / "real.txt", link_root / "link.txt")
    source_value = json.loads(SOURCE_MANIFEST.read_text())
    source_value["entries"] = [
        {"path": "link.txt", "source": "link.txt", "role": "test", "mode": "0644"}
    ]
    source_value["entrypoints"] = [{"name": "test", "path": "link.txt"}]
    source_value["runtime_requirements"] = []
    source_value["policy_references"] = []
    source_path = tmp_path / "links-source.json"
    source_path.write_text(json.dumps(source_value))
    report = build_execution_bundle(source_path, link_root, tmp_path / "link.zip")
    assert not report.valid
    assert "symbolic links" in report.issues[-1].message


def test_builder_rejects_hardlinks_and_special_files(tmp_path: Path) -> None:
    root = tmp_path / "special"
    root.mkdir()
    (root / "real").write_bytes(b"x")
    os.link(root / "real", root / "hard")
    source, _ = _source(
        tmp_path,
        entries=[{"path": "hard", "source": "hard", "role": "test", "mode": "0644"}],
        entrypoints=[{"name": "test", "path": "hard"}],
        runtime_requirements=[],
        policy_references=[],
    )
    report = build_execution_bundle(source, root, tmp_path / "hard.zip")
    assert not report.valid
    assert "hardlinked" in report.issues[-1].message


def test_builder_enforces_declared_size_and_path_limits(tmp_path: Path) -> None:
    root = tmp_path / "limits"
    root.mkdir()
    (root / "large").write_bytes(b"x" * 9)
    source, _ = _source(
        tmp_path,
        entries=[{"path": "large", "source": "large", "role": "test", "mode": "0644"}],
        entrypoints=[{"name": "test", "path": "large"}],
        runtime_requirements=[],
        policy_references=[],
        limits={
            "max_file_count": 1,
            "max_file_bytes": 8,
            "max_total_bytes": 8,
            "max_path_bytes": 512,
            "max_expansion_ratio": 1,
        },
    )
    assert not build_execution_bundle(source, root, tmp_path / "large.zip").valid
    source, _ = _source(
        tmp_path,
        entries=[{"path": "nested/long", "source": "large", "role": "test", "mode": "0644"}],
        entrypoints=[{"name": "test", "path": "nested/long"}],
        runtime_requirements=[],
        policy_references=[],
        limits={
            "max_file_count": 1,
            "max_file_bytes": 16,
            "max_total_bytes": 16,
            "max_path_bytes": 4,
            "max_expansion_ratio": 1,
        },
    )
    assert not build_execution_bundle(source, root, tmp_path / "path-limit.zip").valid


def test_exact_declared_file_and_total_boundaries_are_accepted(tmp_path: Path) -> None:
    root = tmp_path / "boundary"
    root.mkdir()
    (root / "one").write_bytes(b"x" * 8)
    source, _ = _source(
        tmp_path,
        entries=[{"path": "one", "source": "one", "role": "test", "mode": "0644"}],
        entrypoints=[{"name": "test", "path": "one"}],
        runtime_requirements=[],
        policy_references=[],
        limits={
            "max_file_count": 1,
            "max_file_bytes": 8,
            "max_total_bytes": 8,
            "max_path_bytes": 512,
            "max_expansion_ratio": 1,
        },
    )
    assert build_execution_bundle(source, root, tmp_path / "boundary.zip").valid
    assert MAX_FILE_BYTES > 8 and MAX_TOTAL_BYTES > 8


def test_archive_verifier_rejects_corruption_duplicate_paths_links_and_bombs(
    tmp_path: Path,
) -> None:
    corrupt = tmp_path / "corrupt.zip"
    corrupt.write_bytes(b"not a zip")
    assert not verify_execution_bundle_archive(corrupt).valid

    duplicate = tmp_path / "duplicate.zip"
    _zip(
        duplicate,
        [
            ("manifest.json", b"{}", stat.S_IFREG | 0o644),
            ("x", b"a", stat.S_IFREG | 0o644),
            ("x", b"b", stat.S_IFREG | 0o644),
        ],
    )
    assert not verify_execution_bundle_archive(duplicate).valid

    symlink = tmp_path / "symlink.zip"
    _zip(
        symlink,
        [("manifest.json", b"{}", stat.S_IFREG | 0o644), ("link", b"target", stat.S_IFLNK | 0o777)],
    )
    assert not verify_execution_bundle_archive(symlink).valid

    bomb = tmp_path / "bomb.zip"
    data = b"x" * 10000
    _zip(
        bomb,
        [("manifest.json", b"{}", stat.S_IFREG | 0o644), ("payload", data, stat.S_IFREG | 0o644)],
        compression=zipfile.ZIP_DEFLATED,
    )
    assert not verify_execution_bundle_archive(bomb).valid


def test_archive_verifier_rejects_manifest_and_content_mutations(tmp_path: Path) -> None:
    archive, built = _build(tmp_path)
    with zipfile.ZipFile(archive) as original:
        members = [
            (info.filename, original.read(info.filename), (info.external_attr >> 16))
            for info in original.infolist()
        ]
    manifest = json.loads(next(data for name, data, _ in members if name == "manifest.json"))
    manifest["entries"][0]["size_bytes"] += 1
    mutated = tmp_path / "size.zip"
    _zip(
        mutated,
        [("manifest.json", canonicalize(manifest), stat.S_IFREG | 0o644)]
        + [(name, data, mode) for name, data, mode in members if name != "manifest.json"],
    )
    assert not verify_execution_bundle_archive(mutated).valid

    missing = tmp_path / "missing.zip"
    _zip(missing, [(name, data, mode) for name, data, mode in members if name != "tests/test.py"])
    assert not verify_execution_bundle_archive(missing).valid

    assert built.archive_identity is not None


def test_archive_verifier_rejects_undeclared_content_mode_and_digest_changes(
    tmp_path: Path,
) -> None:
    archive, _ = _build(tmp_path)
    with zipfile.ZipFile(archive) as original:
        members = [
            (info.filename, original.read(info.filename), info.external_attr >> 16)
            for info in original.infolist()
        ]
    undeclared = tmp_path / "undeclared.zip"
    _zip(undeclared, [*members, ("extra.txt", b"extra", stat.S_IFREG | 0o644)])
    assert not verify_execution_bundle_archive(undeclared).valid

    changed = tmp_path / "changed-content.zip"
    changed_members = [
        (name, data + b"x" if name == "tests/test.py" else data, mode)
        for name, data, mode in members
    ]
    _zip(changed, changed_members)
    assert not verify_execution_bundle_archive(changed).valid

    mode = tmp_path / "mode.zip"
    mode_members = [
        (name, data, stat.S_IFREG | 0o755 if name == "tests/test.py" else mode)
        for name, data, mode in members
    ]
    _zip(mode, mode_members)
    assert not verify_execution_bundle_archive(mode).valid


def test_unsupported_and_strict_json_inputs_do_not_get_guessed(tmp_path: Path) -> None:
    future = tmp_path / "future.zip"
    _zip(future, [("manifest.json", b'{"schema_version":"9.9"}', stat.S_IFREG | 0o644)])
    report = verify_execution_bundle_archive(future)
    assert report.category == "UNSUPPORTED"

    source = tmp_path / "nonfinite.json"
    source.write_text(
        json.dumps(json.loads(SOURCE_MANIFEST.read_text())).replace(
            '"max_file_count": 32', '"max_file_count": NaN'
        ),
        encoding="utf-8",
    )
    assert not build_execution_bundle(source, SOURCE_ROOT, tmp_path / "nonfinite.zip").valid
