"""Type system for FLEXT infra tests.

Provides TestsFlextInfraTypes, extending TestsFlextTypes with infra-specific
type definitions for infrastructure testing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from flext_tests import FlextTestsTypes

from flext_core import p
from flext_infra import FlextInfraGate, FlextInfraTypes

if TYPE_CHECKING:
    from tests import m


class TestsFlextInfraTypes(FlextTestsTypes, FlextInfraTypes):
    """Type system for FLEXT infra tests - extends TestsFlextTypes.

    Architecture: Extends TestsFlextTypes with infra-specific type definitions.
    All base types from TestsFlextTypes are available through inheritance.
    """

    class Infra(FlextInfraTypes.Infra):
        """Infra-specific type definitions namespace."""

        class Tests:
            """Test-specific type definitions namespace with infra extensions."""

            type ProjectName = str
            "Type for project names in infra testing."
            type DockerImageName = str
            "Type for Docker image names."
            type TestMarker = str
            "Type for test markers (infra, integration, docker, etc.)."

            type GateClass = type[FlextInfraGate]
            type ProjectCheckStub = Callable[..., m.Infra.ProjectResult]
            type RawRunStub = Callable[..., p.Result[m.Cli.CommandOutput]]


t = TestsFlextInfraTypes

__all__: list[str] = ["TestsFlextInfraTypes", "t"]
