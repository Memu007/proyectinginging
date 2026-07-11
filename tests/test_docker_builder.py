from pathlib import Path
from uuid import uuid4

import pytest

from pentestng.sandbox.artifacts import ArtifactStore
from pentestng.sandbox.docker import DockerSandboxRunner
from pentestng.sandbox.models import CommandSpec, ResourceLimits, SandboxPolicy
from pentestng.sandbox.network import NetworkGuard
from pentestng.scope import ScopeManifest


def build_runner(tmp_path) -> DockerSandboxRunner:
    manifest = ScopeManifest.from_dict({"project": {"name": "lab"}})
    image = "tool@sha256:" + "a" * 64
    policy = SandboxPolicy(
        allowed_images=frozenset({image}),
        allowed_executables=frozenset({"tool"}),
        limits=ResourceLimits(cpus=0.25, memory_mb=64, pids=16, tmpfs_mb=8),
    )
    return DockerSandboxRunner(policy, NetworkGuard(manifest), ArtifactStore(tmp_path))


def test_docker_command_has_mandatory_isolation_flags(tmp_path) -> None:
    runner = build_runner(tmp_path)
    image = "tool@sha256:" + "a" * 64
    argv = runner.build_command(
        run_id=str(uuid4()),
        container_name="pentestng-test",
        image=image,
        command=CommandSpec("tool", ("--version",)),
        output_directory=Path(tmp_path),
    )
    rendered = " ".join(argv)
    assert "--network none" in rendered
    assert "--read-only" in argv
    assert "--cap-drop ALL" in rendered
    assert "no-new-privileges:true" in argv
    assert "--pids-limit 16" in rendered
    assert "--memory 64m" in rendered
    assert "--cpus 0.25" in rendered
    assert "/var/run/docker.sock" not in rendered


def test_docker_command_uses_exec_form_not_shell(tmp_path) -> None:
    runner = build_runner(tmp_path)
    image = "tool@sha256:" + "a" * 64
    argv = runner.build_command(
        run_id=str(uuid4()),
        container_name="pentestng-test",
        image=image,
        command=CommandSpec("tool", ("a;b", "$(id)")),
        output_directory=Path(tmp_path),
    )
    assert argv[-3:] == ["tool", "a;b", "$(id)"]
    assert "sh" not in argv
    assert "bash" not in argv


def test_runner_requires_artifact_capacity_for_captured_logs(tmp_path) -> None:
    manifest = ScopeManifest.from_dict({"project": {"name": "lab"}})
    image = "tool@sha256:" + "a" * 64
    policy = SandboxPolicy(
        allowed_images=frozenset({image}),
        allowed_executables=frozenset({"tool"}),
        limits=ResourceLimits(max_output_bytes=100),
    )
    with pytest.raises(ValueError, match="max_file_bytes"):
        DockerSandboxRunner(
            policy,
            NetworkGuard(manifest),
            ArtifactStore(tmp_path, max_file_bytes=99),
        )
