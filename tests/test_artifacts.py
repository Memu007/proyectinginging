import hashlib
from uuid import uuid4

import pytest

from pentestng.sandbox.artifacts import ArtifactCollector, ArtifactLimitExceeded


def test_collects_streams_and_files_with_hashes(tmp_path) -> None:
    collector = ArtifactCollector(tmp_path)
    run = collector.prepare(str(uuid4()), str(uuid4()))
    collector.write_streams(run, b"hello", b"warning")
    result = run.output / "result.txt"
    result.write_text("evidence", encoding="utf-8")
    records = collector.collect(run, ("output",))
    by_path = {record.relative_path: record for record in records}
    assert by_path["stdout.log"].sha256 == hashlib.sha256(b"hello").hexdigest()
    assert by_path["workspace/output/result.txt"].size_bytes == len("evidence")


def test_rejects_symlink_artifact(tmp_path) -> None:
    collector = ArtifactCollector(tmp_path)
    run = collector.prepare(str(uuid4()), str(uuid4()))
    collector.write_streams(run, b"", b"")
    outside = tmp_path / "outside"
    outside.write_text("secret", encoding="utf-8")
    (run.output / "link").symlink_to(outside)
    with pytest.raises(ValueError, match="symbolic"):
        collector.collect(run, ("output",))


def test_enforces_per_file_limit(tmp_path) -> None:
    collector = ArtifactCollector(tmp_path, max_file_bytes=4, max_total_bytes=8)
    run = collector.prepare(str(uuid4()), str(uuid4()))
    with pytest.raises(ArtifactLimitExceeded):
        collector.write_streams(run, b"12345", b"")


def test_rejects_invalid_identifiers(tmp_path) -> None:
    collector = ArtifactCollector(tmp_path)
    with pytest.raises(ValueError, match="session_id"):
        collector.prepare("../escape", str(uuid4()))


def test_enforces_file_count_limit(tmp_path) -> None:
    collector = ArtifactCollector(tmp_path, max_file_bytes=10, max_total_bytes=100, max_files=2)
    run = collector.prepare(str(uuid4()), str(uuid4()))
    collector.write_streams(run, b"", b"")
    (run.output / "one.txt").write_text("1", encoding="utf-8")
    with pytest.raises(ArtifactLimitExceeded, match="file-count"):
        collector.collect(run, ("output",))
