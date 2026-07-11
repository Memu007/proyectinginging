import pytest

from pentestng.sandbox.models import CommandSpec, ResourceLimits, SandboxPolicy


def test_resource_limits_reject_invalid_values() -> None:
    with pytest.raises(ValueError, match="cpus"):
        ResourceLimits(cpus=0)
    with pytest.raises(ValueError, match="memory_mb"):
        ResourceLimits(memory_mb=8)
    with pytest.raises(ValueError, match="timeout_seconds"):
        ResourceLimits(timeout_seconds=0)


def test_command_spec_rejects_nul_bytes() -> None:
    with pytest.raises(ValueError, match="NUL"):
        CommandSpec(executable="python\x00")


def test_policy_rejects_unlisted_image() -> None:
    policy = SandboxPolicy(
        allowed_images=frozenset({"tool@sha256:" + "a" * 64}),
        allowed_executables=frozenset({"tool"}),
    )
    with pytest.raises(PermissionError, match="not allowlisted"):
        policy.authorize("other@sha256:" + "b" * 64, CommandSpec("tool"))


def test_policy_requires_digest_by_default() -> None:
    policy = SandboxPolicy(
        allowed_images=frozenset({"tool:latest"}),
        allowed_executables=frozenset({"tool"}),
    )
    with pytest.raises(PermissionError, match="pinned"):
        policy.authorize("tool:latest", CommandSpec("tool"))


def test_policy_rejects_unlisted_executable() -> None:
    image = "tool@sha256:" + "a" * 64
    policy = SandboxPolicy(
        allowed_images=frozenset({image}),
        allowed_executables=frozenset({"tool"}),
    )
    with pytest.raises(PermissionError, match="Executable"):
        policy.authorize(image, CommandSpec("sh"))


def test_policy_rejects_option_like_image_reference() -> None:
    policy = SandboxPolicy(
        allowed_images=frozenset({"--privileged"}),
        allowed_executables=frozenset({"tool"}),
        require_image_digest=False,
    )
    with pytest.raises(PermissionError, match="invalid"):
        policy.authorize("--privileged", CommandSpec("tool"))
