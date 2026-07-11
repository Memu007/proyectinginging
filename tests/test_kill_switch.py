import pytest

from pentestng.sandbox.kill_switch import KillSwitch


def test_kill_switch_is_one_way_and_keeps_first_reason() -> None:
    switch = KillSwitch()
    assert switch.trigger("operator stop") is True
    assert switch.trigger("second reason") is False
    assert switch.triggered is True
    assert switch.reason == "operator stop"


def test_kill_switch_rejects_empty_reason() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        KillSwitch().trigger("   ")
