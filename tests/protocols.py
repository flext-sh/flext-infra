"""Protocol definitions for FLEXT infra tests.

Provides TestsFlextInfraProtocols, extending TestsFlextProtocols with
infra-specific protocol definitions for infrastructure testing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from flext_tests import FlextTestsProtocols

from flext_infra import FlextInfraProtocols


class TestsFlextInfraProtocols(FlextTestsProtocols, FlextInfraProtocols):
    """Protocol definitions for FLEXT infra tests - extends TestsFlextProtocols.

    Architecture: Extends TestsFlextProtocols with infra-specific protocol definitions.
    All base protocols from TestsFlextProtocols are available through inheritance.
    Protocols cannot import models - only other protocols and types.
    """

    class Infra(FlextInfraProtocols.Infra):
        """Infra-specific protocol definitions."""

        class Tests:
            """Test-specific protocol definitions namespace with infra extensions."""

            @runtime_checkable
            class ProjectValidator(Protocol):
                """Protocol for project validation in infra tests."""

                def validate(self) -> bool:
                    """Validate project configuration.

                    Returns:
                        True if project is valid, False otherwise.

                    """
                    ...

            @runtime_checkable
            class InfraTestRunner(Protocol):
                """Protocol for running infra tests."""

                def run_tests(self) -> int:
                    """Run infra tests.

                    Returns:
                        Exit code (0 for success, non-zero for failure).

                    """
                    ...


p = TestsFlextInfraProtocols
__all__ = ["TestsFlextInfraProtocols", "p"]
