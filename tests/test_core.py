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


def test_orchestrator_verifies_only_with_evidence() -> None:
    session = Session(project_name="lab", scope_digest="abc")
    task = Orchestrator(SingleTaskPlanner(), EvidenceExecutor()).run_once(session)

    assert task is not None
    assert task.state is TaskState.VERIFIED
    assert task.metadata["execution_summary"] == "Inventory written"
