from __future__ import annotations

from flext_cli.base import FlextCliServiceBase
from flext_core import FlextUtilitiesEnforcement as u
from flext_infra.base import FlextInfraServiceBase


def test_service_base_generic_alias_mro_is_permitted() -> None:
    """Generic service-root bases must not trigger facade MRO enforcement."""
    infra_report = u.check(FlextInfraServiceBase)
    cli_report = u.check(FlextCliServiceBase)

    assert not infra_report.violations
    assert not cli_report.violations
