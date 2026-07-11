import pytest

from pentestng.sandbox.models import CommandSpec
from pentestng.sandbox.network import NetworkGuard
from pentestng.scope import ScopeManifest, ScopeViolation


def manifest() -> ScopeManifest:
    return ScopeManifest.from_dict(
        {
            "project": {"name": "lab"},
            "scope": {"allowed_hosts": ["lab.local"], "allowed_ports": [80]},
        }
    )


def test_network_guard_validates_declared_targets() -> None:
    NetworkGuard(manifest()).validate(
        CommandSpec(executable="tool", target_urls=("http://lab.local/path",))
    )


def test_network_guard_rejects_out_of_scope_target() -> None:
    with pytest.raises(ScopeViolation):
        NetworkGuard(manifest()).validate(
            CommandSpec(executable="tool", target_urls=("http://outside.local",))
        )


def test_network_guard_forces_offline_container_network() -> None:
    assert NetworkGuard(manifest()).docker_arguments == ("--network", "none")
