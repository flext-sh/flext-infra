"""Behavioral tests for the public flext-infra service bases.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import override

from flext_tests import tm

from flext_core import r
from flext_infra import p
from flext_infra.base import FlextInfraServiceBase
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase


class TestsFlextInfraServiceBase:
    """Prove canonical service bases preserve scalar result types at runtime."""

    class StringService(FlextInfraServiceBase[str]):
        """Service returning a scalar string through the canonical base."""

        @override
        def execute(self) -> p.Result[str]:
            """Return a successful string result."""
            return r[str].ok("ready")

    class BooleanSelectionService(FlextInfraProjectSelectionServiceBase[bool]):
        """Project-selection service returning a scalar boolean."""

        @override
        def execute(self) -> p.Result[bool]:
            """Return a successful boolean result."""
            return r[bool].ok(True)

    def test_string_service_executes_through_public_base(self) -> None:
        """A string specialization executes without model-only restrictions."""
        result = self.StringService.execute_command(self.StringService())

        tm.that(result.unwrap(), eq="ready")

    def test_boolean_selection_service_executes_through_public_base(self) -> None:
        """A boolean project-selection specialization executes successfully."""
        result = self.BooleanSelectionService.execute_command(
            self.BooleanSelectionService(selected_projects=("flext-core",))
        )

        tm.that(result.unwrap(), eq=True)
