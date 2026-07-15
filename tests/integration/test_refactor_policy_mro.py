"""Integration tests for policy-driven MRO resolution.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest
from flext_tests import tm

from flext_infra.refactor.mro_resolver import FlextInfraRefactorMROResolver
from tests import c


class TestsFlextInfraIntegrationRefactorPolicyMro:
    """Single top-level integration test class for MRO policy resolution."""

    class FlextLdapModels:
        """Stub LDAP models facade."""

    class FlextCliModels:
        """Stub CLI models facade."""

    class DemoMigrationModels(FlextLdapModels, FlextCliModels):
        """Stub composed models facade."""

    class FlextLdapConstants:
        """Stub LDAP constants facade."""

    class FlextCliConstants:
        """Stub CLI constants facade."""

    class DemoMigrationConstants(FlextLdapConstants, FlextCliConstants):
        """Stub composed constants facade."""

    class FlextLdapTypes:
        """Stub LDAP typings facade."""

    class FlextCliTypes:
        """Stub CLI typings facade."""

    class DemoMigrationTypes(FlextLdapTypes, FlextCliTypes):
        """Stub composed typings facade."""

    class FlextLdapProtocols:
        """Stub LDAP protocols facade."""

    class FlextCliProtocols:
        """Stub CLI protocols facade."""

    class DemoMigrationProtocols(FlextLdapProtocols, FlextCliProtocols):
        """Stub composed protocols facade."""

    class FlextLdapUtilities:
        """Stub LDAP utilities facade."""

    class FlextCliUtilities:
        """Stub CLI utilities facade."""

    class DemoMigrationUtilities(FlextLdapUtilities, FlextCliUtilities):
        """Stub composed utilities facade."""

    def test_mro_resolver_accepts_expected_order(self) -> None:
        """Verify matching policy order produces one resolution per facade."""
        resolutions = FlextInfraRefactorMROResolver.resolve(
            family_classes={
                c.Infra.FacadeFamily.C: self.DemoMigrationConstants,
                c.Infra.FacadeFamily.T: self.DemoMigrationTypes,
                c.Infra.FacadeFamily.P: self.DemoMigrationProtocols,
                c.Infra.FacadeFamily.M: self.DemoMigrationModels,
                c.Infra.FacadeFamily.U: self.DemoMigrationUtilities,
            },
            expected_base_chains={
                c.Infra.FacadeFamily.C: ["FlextLdapConstants", "FlextCliConstants"],
                c.Infra.FacadeFamily.T: ["FlextLdapTypes", "FlextCliTypes"],
                c.Infra.FacadeFamily.P: ["FlextLdapProtocols", "FlextCliProtocols"],
                c.Infra.FacadeFamily.M: ["FlextLdapModels", "FlextCliModels"],
                c.Infra.FacadeFamily.U: ["FlextLdapUtilities", "FlextCliUtilities"],
            },
        )
        tm.that(len(resolutions), eq=5)
        model_resolution = next(res for res in resolutions if res.family == "m")
        tm.that(
            model_resolution.expected_bases, eq=("FlextLdapModels", "FlextCliModels")
        )

    def test_mro_resolver_rejects_wrong_order(self) -> None:
        """Verify a reversed facade base order fails validation."""
        with pytest.raises(ValueError, match="direct base order violates policy"):
            FlextInfraRefactorMROResolver.resolve(
                family_classes={
                    c.Infra.FacadeFamily.C: (self.DemoMigrationConstants),
                    c.Infra.FacadeFamily.T: self.DemoMigrationTypes,
                    c.Infra.FacadeFamily.P: (self.DemoMigrationProtocols),
                    c.Infra.FacadeFamily.M: self.DemoMigrationModels,
                    c.Infra.FacadeFamily.U: (self.DemoMigrationUtilities),
                },
                expected_base_chains={
                    c.Infra.FacadeFamily.C: ["FlextLdapConstants", "FlextCliConstants"],
                    c.Infra.FacadeFamily.T: ["FlextLdapTypes", "FlextCliTypes"],
                    c.Infra.FacadeFamily.P: ["FlextLdapProtocols", "FlextCliProtocols"],
                    c.Infra.FacadeFamily.M: ["FlextCliModels", "FlextLdapModels"],
                    c.Infra.FacadeFamily.U: ["FlextLdapUtilities", "FlextCliUtilities"],
                },
            )
