# AUTO-GENERATED FILE — Regenerate with: make gen
"""Models for FLEXT infra tests.

Provides TestsFlextInfraModels, extending TestsFlextModels with infra-specific
model definitions for infrastructure testing and validation.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import m as flext_tests_m

from flext_infra import m as flext_infra_m
from tests._models import TestsFlextInfraModelsBase
from tests._models.semantic_cutover import TestsFlextInfraModelsSemanticCutover


class TestsFlextInfraModels(flext_infra_m):
    """Infra test models composed from the production model facade."""

    class Tests(
        flext_tests_m.Tests,
        TestsFlextInfraModelsBase,
        TestsFlextInfraModelsSemanticCutover,
    ):
        """Tests use inherited flext-tests and production infra models."""


m = TestsFlextInfraModels
__all__: list[str] = ["TestsFlextInfraModels", "m"]
