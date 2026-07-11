from pentestng.core import ExecutionResult, Orchestrator
from pentestng.models import Evidence, Task, TaskState
from pentestng.session import Session


class SingleTaskPlanner:
    def __init__(self) -> None:
        self.used = False

    def next_task(self, session: Session) -> Task | None:
        del session
        if self.used:
            return None
        self.used = True
        return Task(title="Inventory", description="Create a bounded inventory")


class EvidenceExecutor:
    def execute(self, task: Task) -> ExecutionResult:
        del task
        return ExecutionResult(
            succeeded=True,
            summary="Inventory written",
            evidence=(Evidence(kind="artifact", value="inventory.json"),),
        )


class NoEvidenceExecutor:
    def execute(self, task: Task) -> ExecutionResult:
        del task
        return ExecutionResult(succeeded=True, summary="Implemented but not verified")


class RaisingExecutor:
    def execute(self, task: Task) -> ExecutionResult:
        del task
        raise RuntimeError("boom")


def test_orchestrator_verifies_only_with_evidence() -> None:
    session = Session(project_name="lab", scope_digest="abc")
    task = Orchestrator(SingleTaskPlanner(), EvidenceExecutor()).run_once(session)

    assert task is not None
    assert task.state is TaskState.VERIFIED
    assert task.metadata["execution_summary"] == "Inventory written"


def test_orchestrator_does_not_verify_without_evidence() -> None:
    session = Session(project_name="lab", scope_digest="abc")
    task = Orchestrator(SingleTaskPlanner(), NoEvidenceExecutor()).run_once(session)

    assert task is not None
    assert task.state is TaskState.IMPLEMENTED_UNVERIFIED


def test_orchestrator_records_executor_exceptions_as_failures() -> None:
    session = Session(project_name="lab", scope_digest="abc")
    task = Orchestrator(SingleTaskPlanner(), RaisingExecutor()).run_once(session)

    assert task is not None
    assert task.state is TaskState.FAILED
    assert task.metadata["error_type"] == "RuntimeError"
    assert "boom" in task.metadata["execution_summary"]
