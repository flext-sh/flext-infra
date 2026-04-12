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
from tests._constants.domain import TestsFlextInfraConstantsDomain
from tests._constants.fixtures import (
    TestsFlextInfraConstantsFixtures,
)


class TestsFlextInfraConstants(
    FlextTestsConstants,
    FlextInfraConstants,
    TestsFlextInfraConstantsFixtures,
    TestsFlextInfraConstantsDomain,
):
    """Constants for FLEXT infra tests - extends FlextTestsConstants.

    Architecture layer: Layer 0 foundation constants with infra test extensions.
    Architecture: Extends FlextTestsConstants with infra-specific constants.
    All base constants from FlextTestsConstants are available through inheritance.
    """

    class Infra(
        FlextInfraConstants.Infra,
        TestsFlextInfraConstantsFixtures.Infra,
        TestsFlextInfraConstantsDomain.Infra,
    ):
        """Infra-specific test constants namespace.

        All infra-specific test constants are organized under this namespace.
        Access via FlextTestsConstants.Infra.*
        """

        class Tests(
            TestsFlextInfraConstantsFixtures.Infra.Tests,
            TestsFlextInfraConstantsDomain.Infra.Tests,
        ):
            """Test-specific constants namespace with infra extensions.

            All test-specific constants are organized under this namespace.
            Access via FlextTestsConstants.Infra.Tests.* for infra test constants.
            """


c = TestsFlextInfraConstants
__all__: list[str] = ["TestsFlextInfraConstants", "c"]
