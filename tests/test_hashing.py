# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from mncs_validator.hashing import hash_path, sha256_bytes, sha256_file


def test_bytes_and_file_hash_agree(tmp_path: Path) -> None:
    content = b"mncs\n"
    path = tmp_path / "evidence.txt"
    path.write_bytes(content)
    assert sha256_file(path) == sha256_bytes(content)


def test_tree_hash_is_path_sensitive_and_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "a").write_text("same")
    (second / "b").write_text("same")
    assert hash_path(first) == hash_path(first)
    assert hash_path(first) != hash_path(second)


def test_missing_path_raises(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    try:
        hash_path(missing)
    except FileNotFoundError:
        pass
    else:  # pragma: no cover - assertion branch
        raise AssertionError("missing path was hashed")
