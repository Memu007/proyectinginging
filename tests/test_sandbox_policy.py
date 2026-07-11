import pytest

from pentestng.sandbox.models import ExecutionSpec, NetworkAccess
from pentestng.sandbox.policy import SandboxPolicy, SandboxPolicyViolation
from pentestng.scope import ScopeManifest


def manifest() -> ScopeManifest:
    return ScopeManifest.from_dict(
        {
            "project": {"name": "lab"},
            "scope": {
                "allowed_hosts": ["crapi.local"],
                "allowed_ports": [80, 443],
            },
        }
    )


def policy() -> SandboxPolicy:
    return SandboxPolicy(
        allowed_images=frozenset({"alpine:3.20"}),
        allowed_commands={"alpine:3.20": frozenset({"/bin/echo", "/bin/cp", "/bin/sleep"})},
        allowed_environment=frozenset({"MODE"}),
        allowed_docker_networks=frozenset({"crapi-lab"}),
        require_image_digest=False,
    )


def test_unknown_image_rejected() -> None:
    spec = ExecutionSpec(image="ubuntu:latest", argv=("/bin/echo", "ok"))
    with pytest.raises(SandboxPolicyViolation, match="image"):
        policy().validate(spec, manifest())


def test_unknown_command_rejected() -> None:
    spec = ExecutionSpec(image="alpine:3.20", argv=("/bin/sh", "-c", "id"))
    with pytest.raises(SandboxPolicyViolation, match="command"):
        policy().validate(spec, manifest())


def test_network_none_rejects_targets() -> None:
    spec = ExecutionSpec(
        image="alpine:3.20",
        argv=("/bin/echo", "ok"),
        targets=("http://crapi.local",),
    )
    with pytest.raises(SandboxPolicyViolation, match="network=none"):
        policy().validate(spec, manifest())


def test_lab_network_requires_allowlisted_target() -> None:
    spec = ExecutionSpec(
        image="alpine:3.20",
        argv=("/bin/echo", "ok"),
        network=NetworkAccess.LAB,
        docker_network="crapi-lab",
        targets=("https://example.com",),
    )
    with pytest.raises(SandboxPolicyViolation, match="outside"):
        policy().validate(spec, manifest())


def test_lab_network_accepts_authorized_target() -> None:
    spec = ExecutionSpec(
        image="alpine:3.20",
        argv=("/bin/echo", "ok"),
        network=NetworkAccess.LAB,
        docker_network="crapi-lab",
        targets=("http://crapi.local",),
        environment=(("MODE", "test"),),
    )
    policy().validate(spec, manifest())


def test_builtin_docker_network_rejected() -> None:
    custom = SandboxPolicy(
        allowed_images=frozenset({"alpine:3.20"}),
        allowed_commands={"alpine:3.20": frozenset({"/bin/echo"})},
        allowed_docker_networks=frozenset({"host"}),
        require_image_digest=False,
    )
    spec = ExecutionSpec(
        image="alpine:3.20",
        argv=("/bin/echo", "ok"),
        network=NetworkAccess.LAB,
        docker_network="host",
        targets=("http://crapi.local",),
    )
    with pytest.raises(SandboxPolicyViolation, match="built-in"):
        custom.validate(spec, manifest())


def test_digest_pinning_is_required_by_default() -> None:
    strict = SandboxPolicy(
        allowed_images=frozenset({"alpine:3.20"}),
        allowed_commands={"alpine:3.20": frozenset({"/bin/echo"})},
    )
    spec = ExecutionSpec(image="alpine:3.20", argv=("/bin/echo", "ok"))
    with pytest.raises(SandboxPolicyViolation, match="sha256"):
        strict.validate(spec, manifest())
