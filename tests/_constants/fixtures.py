"""Fixtures test constants mixin for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Final


class TestsFlextInfraConstantsFixtures:
    """Constants mixin for fixtures."""

    class Fixtures:
        """Shared fixture constants for behavior-driven tests."""

        class Workspace:
            PROJECT_CLASS: Final[str] = "platform"
            PROJECT_STACK: Final[str] = "py"
            PROJECT_PACKAGE_NAME: Final[str] = ""

        class Deps:
            PROJECT_NAME: Final[str] = "proj"
            EMPTY_PROJECT_NAME: Final[str] = "no-pyproject"
            PROJECT_DIRNAME: Final[str] = "project"
            REPORT_FILENAME: Final[str] = ".deptry-report.json"
            INVALID_JSON: Final[str] = "not valid json"
            SELECTOR_FAILED: Final[str] = "failed"
            RUNNER_FAILED: Final[str] = "deptry crash"

        class Codegen:
            PROJECT_A_NAME: Final[str] = "project-a"
            PROJECT_B_NAME: Final[str] = "project-b"
            DEMO_PROJECT_NAME: Final[str] = "demo"
            PROJECT_STACK: Final[str] = "python/flext"
            PACKAGE_NAME: Final[str] = "demo_pkg"

            class LazyInit:
                PROJECT_NAME: Final[str] = "demo"
                PACKAGE_NAME: Final[str] = "test_pkg"
                ROOT_PACKAGE_NAME: Final[str] = "flext_demo"
                MODELS_CLASS: Final[str] = "TestPkgModels"
                MODELS_ALIAS: Final[str] = "m"
                CHILD_SERVICE_CLASS: Final[str] = "TestPkgSubService"
                CHILD_SERVICE_ALIAS: Final[str] = "s"
                TESTS_TYPES_CLASS: Final[str] = "TestsFlextDemoTypes"
                TESTS_TYPES_ALIAS: Final[str] = "t"
                EXAMPLES_UTILITIES_CLASS: Final[str] = "ExamplesFlextDemoUtilities"
                EXAMPLES_UTILITIES_ALIAS: Final[str] = "u"
                VERSION: Final[str] = "1.0.0"
                VERSION_INFO: Final[str] = "(1, 0, 0)"

        class Refactor:
            PROJECT_NAME: Final[str] = "flext-demo"
            PACKAGE_NAME: Final[str] = "demo_pkg"
            CONSTANTS_CLASS: Final[str] = "FlextDemoConstants"
            FACADE_ALIAS: Final[str] = "c"
            SYMBOL_NAME: Final[str] = "FOO"
            SYMBOL_VALUE: Final[str] = "value"
