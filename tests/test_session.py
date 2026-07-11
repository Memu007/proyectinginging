import pytest

from pentestng.models import Task
from pentestng.session import JsonSessionStore, Session


def test_session_round_trip(tmp_path) -> None:
    store = JsonSessionStore(tmp_path)
    session = Session(project_name="lab", scope_digest="abc123")
    session.add_task(Task(title="Recon", description="Map the target"))

    store.save(session)
    restored = store.load(session.id)

    assert restored.id == session.id
    assert restored.tasks[0].title == "Recon"


def test_session_id_cannot_escape_store_root(tmp_path) -> None:
    store = JsonSessionStore(tmp_path)
    with pytest.raises(ValueError, match="valid UUID"):
        store.load("../outside")
