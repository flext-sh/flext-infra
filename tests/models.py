# AUTO-GENERATED FILE — Regenerate with: make gen
"""Models for FLEXT infra tests.

Provides TestsFlextInfraModels, extending TestsFlextModels with infra-specific
model definitions for infrastructure testing and validation.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import m as flext_tests_m

from flext_infra import FlextInfraModels
from tests._models import (
    TestsFlextInfraModelsBase,
    TestsFlextInfraModelsSemanticCutover,
)


class TestsFlextInfraModels(FlextInfraModels):
    """Infra test models composed from the production model facade."""

    class Tests(
        flext_tests_m.Tests,
        TestsFlextInfraModelsBase,
        TestsFlextInfraModelsSemanticCutover,
    ):
        """Tests use inherited flext-tests and production infra models."""


m = TestsFlextInfraModels
__all__: list[str] = ["TestsFlextInfraModels", "m"]
