"""Models for FLEXT infra tests.

Provides TestsFlextInfraModels, extending TestsFlextModels with infra-specific
model definitions for infrastructure testing and validation.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_tests import FlextTestsModels

from flext_core import r
from flext_infra import (
    m,
)


class TestsFlextInfraModels(m, FlextTestsModels):
    """Infra test models extending TestsFlextModels with infra-specific models.

    Architecture: Extends TestsFlextModels with infra-specific model definitions.
    All base models from TestsFlextModels are available through inheritance.
    """

    class Infra(m.Infra):
        """Infra-specific models namespace."""

        class Tests:
            """Test-specific models namespace with infra extensions."""

            class ProjectInfo(FlextTestsModels.Value):
                """Project information model for infra testing."""

                name: str
                path: str
                version: str = "0.1.0"
                is_active: bool = True

            class InfraConfig(FlextTestsModels.Value):
                """Infrastructure configuration model."""

                project_name: str
                docker_enabled: bool = False
                test_timeout: int = 60
                parallel_tests: bool = True

            class TestResult(FlextTestsModels.Value):
                """Test result model for infra tests."""

                test_name: str
                passed: bool
                duration_ms: float = 0.0
                error_message: str | None = None

            class RunProjectsMock:
                """Stateful fake for workspace checker project loops."""

                def __init__(
                    self,
                    passed: bool | None = None,
                    error_msg: str | None = None,
                ) -> None:
                    self.passed = True if passed is None else passed
                    self.error_msg = error_msg
                    self.captured_projects: list[str] = []
                    self.captured_fail_fast = False

                def __call__(
                    self,
                    projects: Sequence[str],
                    gates: Sequence[str],
                    *,
                    reports_dir: Path | None = None,
                    fail_fast: bool = False,
                    **_kwargs: object,
                ) -> r[Sequence[m.Infra.ProjectResult]]:
                    del gates, reports_dir, _kwargs
                    self.captured_projects = list(projects)
                    self.captured_fail_fast = fail_fast
                    if self.error_msg:
                        return r[Sequence[m.Infra.ProjectResult]].fail(self.error_msg)
                    result = m.Infra.ProjectResult(project="test-project")
                    if not self.passed:
                        result.gates["test"] = m.Infra.GateExecution(
                            result=m.Infra.GateResult(
                                gate="test",
                                project="test-project",
                                passed=False,
                                errors=(),
                                duration=0.0,
                            ),
                            issues=(),
                            raw_output="",
                        )
                    return r[Sequence[m.Infra.ProjectResult]].ok([result])


m = TestsFlextInfraModels

__all__ = ["TestsFlextInfraModels", "m"]
