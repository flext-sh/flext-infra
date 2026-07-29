"""Tests for the MRO service-base alias."""

from __future__ import annotations

from flext_cli import s as cli_service_base
from flext_infra import FlextInfraServiceBase
from flext_tests import tm
from tests import u


def test_service_base_generic_alias_mro_is_permitted() -> None:
    """Generic service-root bases must not trigger facade MRO enforcement."""
    infra_report = u.check(FlextInfraServiceBase)
    cli_report = u.check(cli_service_base)

    tm.that(not infra_report.violations, eq=True)
    tm.that(not cli_report.violations, eq=True)
