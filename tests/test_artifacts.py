import hashlib
import os
from uuid import uuid4

import pytest

from pentestng.sandbox.artifacts import ArtifactPolicyError, ArtifactStore


def test_write_bytes_hashes_and_persists(tmp_path) -> None:
    run_id = str(uuid4())
    record = ArtifactStore(tmp_path).write_bytes(run_id, "logs/output.txt", b"hello")
    assert record.sha256 == hashlib.sha256(b"hello").hexdigest()
    assert (tmp_path / run_id / "logs" / "output.txt").read_bytes() == b"hello"


def test_artifact_paths_cannot_escape_store(tmp_path) -> None:
    with pytest.raises(ArtifactPolicyError, match="relative"):
        ArtifactStore(tmp_path).write_bytes(str(uuid4()), "../escape", b"x")


def test_collect_directory_rejects_symlinks(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    target = tmp_path / "secret"
    target.write_text("secret")
    try:
        os.symlink(target, source / "link")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(ArtifactPolicyError, match="symbolic"):
        ArtifactStore(tmp_path / "store").collect_directory(str(uuid4()), source)


def test_collect_directory_enforces_size_limit(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "large.bin").write_bytes(b"12345")
    store = ArtifactStore(tmp_path / "store", max_file_bytes=4)
    with pytest.raises(ArtifactPolicyError, match="max_file_bytes"):
        store.collect_directory(str(uuid4()), source)


def test_collect_directory_hashes_regular_files(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "result.json").write_text('{"ok": true}')
    run_id = str(uuid4())
    records = ArtifactStore(tmp_path / "store").collect_directory(run_id, source)
    assert records[0].relative_path == "output/result.json"
    assert records[0].size_bytes > 0
