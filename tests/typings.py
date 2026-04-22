"""Type system for FLEXT infra tests.

Provides TestsFlextInfraTypes, extending TestsFlextTypes with infra-specific
type definitions for infrastructure testing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import FlextTestsTypes

from flext_infra import t


class TestsFlextInfraTypes(FlextTestsTypes, t):
    """Type system for FLEXT infra tests."""

    __test__ = False

    class Infra(t.Infra):
        """Infra-specific type definitions namespace."""

        class Tests:
            """Tests use inherited flext-tests and production typing contracts."""


t = TestsFlextInfraTypes

__all__: list[str] = ["TestsFlextInfraTypes", "t"]
