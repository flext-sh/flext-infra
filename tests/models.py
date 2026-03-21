"""Models for FLEXT infra tests.

Provides FlextInfraTestModels, extending TestsFlextModels with infra-specific
model definitions for infrastructure testing and validation.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import FlextTestsModels as FlextTestModels

from flext_infra import FlextInfraModels


class FlextInfraTestModels(FlextTestModels):
    """Infra test models extending FlextTestModels with infra-specific models.

    Architecture: Extends FlextTestModels with infra-specific model definitions.
    All base models from FlextTestModels are available through inheritance.
    """

    class Infra(FlextInfraModels.Infra):
        """Infra-specific models namespace."""

        class Tests:
            """Test-specific models namespace with infra extensions."""

            class ProjectInfo(FlextTestModels.Value):
                """Project information model for infra testing."""

                name: str
                path: str
                version: str = "0.1.0"
                is_active: bool = True

            class InfraConfig(FlextTestModels.Value):
                """Infrastructure configuration model."""

                project_name: str
                docker_enabled: bool = False
                test_timeout: int = 60
                parallel_tests: bool = True

            class TestResult(FlextTestModels.Value):
                """Test result model for infra tests."""

                test_name: str
                passed: bool
                duration_ms: float = 0.0
                error_message: str | None = None


m = FlextInfraTestModels

__all__ = ["FlextInfraTestModels", "m"]
