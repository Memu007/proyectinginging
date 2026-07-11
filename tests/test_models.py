import pytest

from pentestng.models import Evidence, Task, TaskState


def test_verified_requires_evidence() -> None:
    task = Task(title="Map API", description="Enumerate authorized routes")
    task.transition(TaskState.IN_PROGRESS)
    with pytest.raises(ValueError, match="without evidence"):
        task.transition(TaskState.VERIFIED)


def test_verified_with_evidence() -> None:
    task = Task(title="Map API", description="Enumerate authorized routes")
    task.transition(TaskState.IN_PROGRESS)
    task.add_evidence(Evidence(kind="tool-output", value="routes.json"))
    task.transition(TaskState.VERIFIED)
    assert task.state is TaskState.VERIFIED
