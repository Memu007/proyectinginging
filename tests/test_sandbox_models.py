import pytest

from pentestng.sandbox.models import ExecutionSpec, ResourceLimits


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("cpus", 0),
        ("memory_mb", 32),
        ("pids", 1),
        ("timeout_seconds", 0),
        ("tmpfs_mb", 4),
    ],
)
def test_invalid_resource_limits_rejected(field: str, value: int | float) -> None:
    kwargs = {field: value}
    with pytest.raises(ValueError):
        ResourceLimits(**kwargs)


def test_execution_spec_rejects_empty_argv() -> None:
    with pytest.raises(ValueError, match="executable"):
        ExecutionSpec(image="alpine:3.20", argv=())


def test_execution_spec_rejects_artifact_traversal() -> None:
    with pytest.raises(ValueError, match="artifact_paths"):
        ExecutionSpec(image="alpine:3.20", argv=("/bin/echo", "ok"), artifact_paths=("../x",))


def test_execution_spec_rejects_duplicate_environment_keys() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        ExecutionSpec(
            image="alpine:3.20",
            argv=("/bin/echo", "ok"),
            environment=(("MODE", "a"), ("MODE", "b")),
        )


def test_execution_spec_rejects_environment_newlines() -> None:
    with pytest.raises(ValueError, match="environment value"):
        ExecutionSpec(
            image="alpine:3.20",
            argv=("/bin/echo", "ok"),
            environment=(("MODE", "safe\nINJECTED=yes"),),
        )
