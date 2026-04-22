"""Models for FLEXT infra tests.

Provides TestsFlextInfraModels, extending TestsFlextModels with infra-specific
model definitions for infrastructure testing and validation.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import FlextTestsModels

from flext_infra import m


class TestsFlextInfraModels(m, FlextTestsModels):
    """Infra test models extending flext-tests and production models."""

    __test__ = False

    class Infra(m.Infra):
        """Infra-specific models namespace."""

        class Tests:
            """Tests use inherited flext-tests and production infra models."""


m = TestsFlextInfraModels

__all__: list[str] = ["TestsFlextInfraModels", "m"]
