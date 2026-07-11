import pytest

from pentestng.scope import ScopeManifest, ScopeViolation


def build_manifest() -> ScopeManifest:
    return ScopeManifest.from_dict(
        {
            "project": {"name": "lab"},
            "scope": {
                "allowed_hosts": ["crapi.local"],
                "allowed_networks": ["172.20.0.0/24"],
                "allowed_ports": [80, 443, 8888],
            },
        }
    )


def test_authorizes_exact_host() -> None:
    build_manifest().authorize_url("http://crapi.local/api")


def test_authorizes_ip_inside_network() -> None:
    build_manifest().authorize_url("http://172.20.0.12:8888/health")


def test_rejects_unlisted_host() -> None:
    with pytest.raises(ScopeViolation):
        build_manifest().authorize_url("https://example.com")


def test_rejects_unlisted_port() -> None:
    with pytest.raises(ScopeViolation):
        build_manifest().authorize_url("http://crapi.local:9000")


def test_rejects_malformed_port() -> None:
    with pytest.raises(ScopeViolation, match="invalid port"):
        build_manifest().authorize_url("http://crapi.local:notaport")


def test_rejects_nonpositive_limits() -> None:
    with pytest.raises(ValueError, match="requests_per_second"):
        ScopeManifest.from_dict(
            {"project": {"name": "lab"}, "limits": {"requests_per_second": 0}}
        )
    with pytest.raises(ValueError, match="runtime_minutes"):
        ScopeManifest.from_dict(
            {"project": {"name": "lab"}, "limits": {"runtime_minutes": 0}}
        )
