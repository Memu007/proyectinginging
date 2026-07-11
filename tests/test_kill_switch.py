import pytest

from pentestng.sandbox.kill_switch import KillSwitch, KillSwitchTriggered


def test_kill_switch_records_first_reason() -> None:
    switch = KillSwitch()
    switch.trip("operator stop")
    switch.trip("ignored second reason")
    assert switch.is_tripped
    assert switch.reason == "operator stop"


def test_kill_switch_refuses_future_execution() -> None:
    switch = KillSwitch()
    switch.trip("scope changed")
    with pytest.raises(KillSwitchTriggered, match="scope changed"):
        switch.raise_if_tripped()


def test_kill_switch_requires_reason() -> None:
    with pytest.raises(ValueError, match="reason"):
        KillSwitch().trip(" ")
