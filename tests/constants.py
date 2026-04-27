"""Constants for FLEXT infra tests.

Provides TestsFlextInfraConstants, extending FlextTestsConstants with
infra-specific constants for infrastructure testing, project names, and test
markers.

Copyright (FlextTestsConstants) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import FlextTestsConstants

from flext_infra import c
from tests import (
    TestsFlextInfraConstantsDomain,
    TestsFlextInfraConstantsFixtures,
)


class TestsFlextInfraConstants(
    FlextTestsConstants,
    c,
):
    """Constants for FLEXT infra tests - extends FlextTestsConstants.

    Architecture layer: Layer 0 foundation constants with infra test extensions.
    Architecture: Extends FlextTestsConstants with infra-specific constants.
    All base constants from FlextTestsConstants are available through inheritance.
    """

    __test__ = False

    class Tests(
        FlextTestsConstants.Tests,
        TestsFlextInfraConstantsFixtures,
        TestsFlextInfraConstantsDomain,
    ):
        """Test-specific constants namespace with infra extensions.

        All test-specific constants are organized under this namespace.
        Access via FlextTestsConstants.Tests.* for infra test constants.
        """


c = TestsFlextInfraConstants
__all__: list[str] = ["TestsFlextInfraConstants", "c"]
