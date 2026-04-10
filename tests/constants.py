"""Constants for FLEXT infra tests.

Provides TestsFlextInfraConstants, extending FlextTestsConstants with
infra-specific constants for infrastructure testing, project names, and test
markers.

Copyright (FlextTestsConstants) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import FlextTestsConstants

from flext_infra import FlextInfraConstants
from tests._constants.domain import (
    TestsFlextInfraConstantsMarkers,
    TestsFlextInfraConstantsPaths,
    TestsFlextInfraConstantsProjects,
    TestsFlextInfraConstantsVersions,
)
from tests._constants.fixtures import (
    TestsFlextInfraConstantsFixtures,
)


class TestsFlextInfraConstants(
    FlextTestsConstants,
    FlextInfraConstants,
    TestsFlextInfraConstantsFixtures,
    TestsFlextInfraConstantsProjects,
    TestsFlextInfraConstantsMarkers,
    TestsFlextInfraConstantsVersions,
    TestsFlextInfraConstantsPaths,
):
    """Constants for FLEXT infra tests - extends FlextTestsConstants.

    Architecture layer: Layer 0 foundation constants with infra test extensions.
    Architecture: Extends FlextTestsConstants with infra-specific constants.
    All base constants from FlextTestsConstants are available through inheritance.
    """

    class Infra(
        FlextInfraConstants.Infra,
        TestsFlextInfraConstantsFixtures.Infra,
        TestsFlextInfraConstantsProjects.Infra,
        TestsFlextInfraConstantsMarkers.Infra,
        TestsFlextInfraConstantsVersions.Infra,
        TestsFlextInfraConstantsPaths.Infra,
    ):
        """Infra-specific test constants namespace.

        All infra-specific test constants are organized under this namespace.
        Access via FlextTestsConstants.Infra.*
        """

        class Tests(
            TestsFlextInfraConstantsFixtures.Infra.Tests,
            TestsFlextInfraConstantsProjects.Infra.Tests,
            TestsFlextInfraConstantsMarkers.Infra.Tests,
            TestsFlextInfraConstantsVersions.Infra.Tests,
            TestsFlextInfraConstantsPaths.Infra.Tests,
        ):
            """Test-specific constants namespace with infra extensions.

            All test-specific constants are organized under this namespace.
            Access via FlextTestsConstants.Infra.Tests.* for infra test constants.
            """


c = TestsFlextInfraConstants
__all__ = ["TestsFlextInfraConstants", "c"]
