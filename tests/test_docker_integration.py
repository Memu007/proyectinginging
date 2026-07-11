import shutil
import subprocess
import threading
import time

import pytest

from pentestng.sandbox.artifacts import ArtifactStore
from pentestng.sandbox.docker import DockerSandboxRunner
from pentestng.sandbox.kill_switch import KillSwitch
from pentestng.sandbox.models import CommandSpec, ExecutionStatus, ResourceLimits, SandboxPolicy
from pentestng.sandbox.network import NetworkGuard
from pentestng.scope import ScopeManifest

IMAGE = "python:3.11-alpine"


def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(
            ["docker", "info"], capture_output=True, timeout=5, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


pytestmark = [pytest.mark.docker, pytest.mark.skipif(not docker_available(), reason="Docker unavailable")]


def runner(tmp_path, timeout: float = 10) -> DockerSandboxRunner:
    manifest = ScopeManifest.from_dict({"project": {"name": "docker-test"}})
    policy = SandboxPolicy(
        allowed_images=frozenset({IMAGE}),
        allowed_executables=frozenset({"python"}),
        require_image_digest=False,
        limits=ResourceLimits(timeout_seconds=timeout, memory_mb=128),
    )
    return DockerSandboxRunner(
        policy,
        NetworkGuard(manifest),
        ArtifactStore(tmp_path / "artifacts"),
        workspace_root=tmp_path,
    )


def test_docker_runner_captures_output_and_artifact(tmp_path) -> None:
    result = runner(tmp_path).run(
        image=IMAGE,
        command=CommandSpec(
            "python",
            (
                "-c",
                "from pathlib import Path; Path('/artifacts/result.txt').write_text('ok'); print('hello')",
            ),
        ),
    )
    assert result.status is ExecutionStatus.SUCCEEDED
    assert "hello" in result.stdout
    assert any(record.relative_path == "output/result.txt" for record in result.artifacts)


def test_docker_runner_enforces_timeout(tmp_path) -> None:
    result = runner(tmp_path, timeout=0.3).run(
        image=IMAGE,
        command=CommandSpec("python", ("-c", "import time; time.sleep(10)")),
    )
    assert result.status is ExecutionStatus.TIMED_OUT


def test_docker_runner_honors_kill_switch(tmp_path) -> None:
    switch = KillSwitch()
    timer = threading.Thread(target=lambda: (time.sleep(0.3), switch.trigger("test stop")))
    timer.start()
    result = runner(tmp_path, timeout=10).run(
        image=IMAGE,
        command=CommandSpec("python", ("-c", "import time; time.sleep(10)")),
        kill_switch=switch,
    )
    timer.join()
    assert result.status is ExecutionStatus.CANCELLED
    assert result.error == "test stop"
