from pentestng.llm.base import LLMRequest
from pentestng.llm.mock import MockProvider


def test_mock_provider_is_deterministic() -> None:
    provider = MockProvider("planned-task")
    response = provider.complete(LLMRequest(system="system", prompt="next"))

    assert response.text == "planned-task"
    assert response.provider == "mock"
