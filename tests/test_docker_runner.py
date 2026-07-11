from uuid import uuid4

import pytest

from pentestng.sandbox.artifacts import ArtifactCollector
from pentestng.sandbox.docker import DockerRunner, SandboxUnavailable
from pentestng.sandbox.models import ExecutionSpec, NetworkAccess, ResourceLimits
from pentestng.sandbox.policy import SandboxPolicy


def runner(tmp_path) -> DockerRunner:
    return DockerRunner(
        SandboxPolicy(
            allowed_images=frozenset({"alpine:3.20"}),
            allowed_commands={"alpine:3.20": frozenset({"/bin/echo"})},
            allowed_environment=frozenset({"MODE"}),
            allowed_docker_networks=frozenset({"crapi-lab"}),
            require_image_digest=False,
        ),
        ArtifactCollector(tmp_path),
    )


def test_build_command_has_mandatory_isolation_flags(tmp_path) -> None:
    item = runner(tmp_path)
    run = item.collector.prepare(str(uuid4()), str(uuid4()))
    spec = ExecutionSpec(
        image="alpine:3.20",
        argv=("/bin/echo", "ok"),
        limits=ResourceLimits(cpus=0.5, memory_mb=128, pids=32, timeout_seconds=5),
        environment=(("MODE", "test"),),
    )
    command = item.build_command(spec, run, "pentestng-test")
    joined = " ".join(command)
    assert "--read-only" in command
    assert "--cap-drop ALL" in joined
    assert "no-new-privileges" in command
    assert "--network none" in joined
    assert "--pull never" in joined
    user_value = command[command.index("--user") + 1]
    assert user_value != "0:0"
    mounts = [command[index + 1] for index, value in enumerate(command) if value == "--mount"]
    assert all("docker.sock" not in mount for mount in mounts)
    assert "MODE=test" not in joined
    assert command[-3:] == ["alpine:3.20", "/bin/echo", "ok"]


def test_lab_network_is_named_not_host(tmp_path) -> None:
    item = runner(tmp_path)
    run = item.collector.prepare(str(uuid4()), str(uuid4()))
    spec = ExecutionSpec(
        image="alpine:3.20",
        argv=("/bin/echo", "ok"),
        network=NetworkAccess.LAB,
        docker_network="crapi-lab",
        targets=("http://crapi.local",),
    )
    command = item.build_command(spec, run, "pentestng-test")
    assert command[command.index("--network") + 1] == "crapi-lab"


def test_remote_docker_daemon_is_rejected(tmp_path) -> None:
    with pytest.raises(ValueError, match="local unix"):
        DockerRunner(
            SandboxPolicy(
                allowed_images=frozenset(),
                allowed_commands={},
            ),
            ArtifactCollector(tmp_path),
            docker_host="tcp://docker.example:2375",
        )


def test_stream_capture_trips_limit(tmp_path) -> None:
    from io import BytesIO
    from threading import Event

    item = DockerRunner(
        SandboxPolicy(allowed_images=frozenset(), allowed_commands={}),
        ArtifactCollector(tmp_path, max_file_bytes=4, max_total_bytes=8),
    )
    buffer = bytearray()
    overflow = Event()
    item._capture_stream(BytesIO(b"12345"), buffer, overflow)
    assert overflow.is_set()
    assert bytes(buffer) == b"1234"


def test_non_internal_lab_network_is_rejected(tmp_path, monkeypatch) -> None:
    import subprocess

    class Result:
        returncode = 0
        stdout = b"false\n"
        stderr = b""

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: Result())
    item = runner(tmp_path)
    with pytest.raises(SandboxUnavailable, match="--internal"):
        item._ensure_internal_network("crapi-lab")
