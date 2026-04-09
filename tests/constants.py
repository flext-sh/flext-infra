"""Constants for FLEXT infra tests.

Provides TestsFlextInfraConstants, extending FlextTestsConstants with
infra-specific constants for infrastructure testing, project names, and test
markers.

Copyright (FlextTestsConstants) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Final

from flext_tests import FlextTestsConstants

from flext_infra import FlextInfraConstants


class TestsFlextInfraConstants(FlextTestsConstants, FlextInfraConstants):
    """Constants for FLEXT infra tests - extends FlextTestsConstants.

    Architecture layer: Layer 0 foundation constants with infra test extensions.
    Architecture: Extends FlextTestsConstants with infra-specific constants.
    All base constants from FlextTestsConstants are available through inheritance.
    """

    class Infra(FlextInfraConstants.Infra):
        """Infra-specific test constants namespace.

        All infra-specific test constants are organized under this namespace.
        Access via FlextTestsConstants.Infra.*
        """

        class Tests:
            """Test-specific constants namespace with infra extensions.

            All test-specific constants are organized under this namespace.
            Access via FlextTestsConstants.Infra.Tests.* for infra test constants.
            """

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
                        EXAMPLES_UTILITIES_CLASS: Final[str] = (
                            "ExamplesFlextDemoUtilities"
                        )
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

            class Projects:
                """Project names and identifiers for infra testing."""

                FLEXT_CORE: Final[str] = "flext-core"
                FLEXT_API: Final[str] = "flext-api"
                FLEXT_CLI: Final[str] = "flext-cli"
                FLEXT_MELTANO: Final[str] = "flext-meltano"
                FLEXT_LDAP: Final[str] = "flext-ldap"
                FLEXT_LDIF: Final[str] = "flext-ldif"
                FLEXT_OBSERVABILITY: Final[str] = "flext-observability"
                FLEXT_QUALITY: Final[str] = "flext-quality"

                ALL_PROJECTS: Final[tuple[str, ...]] = (
                    FLEXT_CORE,
                    FLEXT_API,
                    FLEXT_CLI,
                    FLEXT_MELTANO,
                    FLEXT_LDAP,
                    FLEXT_LDIF,
                    FLEXT_OBSERVABILITY,
                    FLEXT_QUALITY,
                )

            class Markers:
                """Test markers for infra test categorization."""

                INFRA: Final[str] = "infra"
                INTEGRATION: Final[str] = "integration"
                DOCKER: Final[str] = "docker"
                SLOW: Final[str] = "slow"
                REQUIRES_NETWORK: Final[str] = "requires_network"
                REQUIRES_DOCKER: Final[str] = "requires_docker"

            class Versions:
                """Version strings for infra components."""

                PYTHON_MIN: Final[str] = "3.13"
                PYTHON_RECOMMENDED: Final[str] = "3.13"
                POETRY_MIN: Final[str] = "1.8"
                RUFF_MIN: Final[str] = "0.1"
                MYPY_MIN: Final[str] = "1.0"

            class Paths:
                """Path constants for infra testing."""

                DOCKER_COMPOSE_DIR: Final[str] = "docker"
                TESTS_DIR: Final[str] = "tests"
                INFRA_TESTS_DIR: Final[str] = "tests/infra"
                FIXTURES_DIR: Final[str] = "tests/fixtures"
                INTEGRATION_DIR: Final[str] = "tests/integration"


c = TestsFlextInfraConstants
__all__ = ["TestsFlextInfraConstants", "c"]
