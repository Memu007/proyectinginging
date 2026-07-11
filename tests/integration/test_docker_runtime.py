import os
from threading import Thread
from time import sleep
from uuid import uuid4

import pytest

from pentestng.sandbox.artifacts import ArtifactCollector
from pentestng.sandbox.docker import DockerRunner
from pentestng.sandbox.kill_switch import KillSwitch
from pentestng.sandbox.models import ExecutionSpec, NetworkAccess, ResourceLimits
from pentestng.sandbox.policy import SandboxPolicy
from pentestng.scope import ScopeManifest

pytestmark = pytest.mark.docker_integration


def build_runner(tmp_path) -> DockerRunner:
    return DockerRunner(
        SandboxPolicy(
            allowed_images=frozenset({"alpine:3.20"}),
            allowed_commands={"alpine:3.20": frozenset({"/bin/cp", "/bin/echo", "/bin/sleep"})},
            allowed_docker_networks=frozenset({"pentestng-ci"}),
            require_image_digest=False,
        ),
        ArtifactCollector(tmp_path),
        poll_interval=0.05,
    )


def manifest() -> ScopeManifest:
    return ScopeManifest.from_dict({"project": {"name": "docker-integration"}})


def require_docker(runner: DockerRunner) -> None:
    if os.environ.get("PENTESTNG_DOCKER_INTEGRATION") != "1" or not runner.is_available():
        pytest.skip("Docker integration tests are opt-in and require a working daemon")


def test_container_writes_hashed_artifact(tmp_path) -> None:
    runner = build_runner(tmp_path)
    require_docker(runner)
    result = runner.run(
        ExecutionSpec(
            image="alpine:3.20",
            argv=("/bin/cp", "/etc/alpine-release", "/workspace/output/alpine-release"),
            limits=ResourceLimits(timeout_seconds=20),
        ),
        manifest(),
        session_id=str(uuid4()),
        task_id=str(uuid4()),
    )
    assert result.succeeded
    assert any(record.relative_path.endswith("alpine-release") for record in result.artifacts)


def test_container_timeout_is_enforced(tmp_path) -> None:
    runner = build_runner(tmp_path)
    require_docker(runner)
    result = runner.run(
        ExecutionSpec(
            image="alpine:3.20",
            argv=("/bin/sleep", "10"),
            limits=ResourceLimits(timeout_seconds=1),
        ),
        manifest(),
        session_id=str(uuid4()),
        task_id=str(uuid4()),
    )
    assert result.timed_out
    assert not result.succeeded


def test_kill_switch_stops_running_container(tmp_path) -> None:
    runner = build_runner(tmp_path)
    require_docker(runner)
    switch = KillSwitch()
    thread = Thread(target=lambda: (sleep(0.3), switch.trip("operator stop")), daemon=True)
    thread.start()
    result = runner.run(
        ExecutionSpec(
            image="alpine:3.20",
            argv=("/bin/sleep", "10"),
            limits=ResourceLimits(timeout_seconds=20),
        ),
        manifest(),
        session_id=str(uuid4()),
        task_id=str(uuid4()),
        kill_switch=switch,
    )
    thread.join(timeout=2)
    assert result.cancelled
    assert "operator stop" in result.summary


def test_internal_lab_network_is_accepted(tmp_path) -> None:
    runner = build_runner(tmp_path)
    require_docker(runner)
    result = runner.run(
        ExecutionSpec(
            image="alpine:3.20",
            argv=("/bin/echo", "network-policy-ok"),
            network=NetworkAccess.LAB,
            docker_network="pentestng-ci",
            targets=("http://crapi.local",),
            limits=ResourceLimits(timeout_seconds=20),
        ),
        ScopeManifest.from_dict(
            {
                "project": {"name": "docker-integration"},
                "scope": {"allowed_hosts": ["crapi.local"], "allowed_ports": [80]},
            }
        ),
        session_id=str(uuid4()),
        task_id=str(uuid4()),
    )
    assert result.succeeded
