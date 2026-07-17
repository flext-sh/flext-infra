"""Project-level integration tests for class nesting transformation.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm

from flext_infra.transformers.class_nesting import (
    FlextInfraRefactorClassNestingTransformer,
)
from tests import t


class TestsFlextInfraIntegrationRefactorNestingProject:
    """Test class nesting across representative project source."""

    @staticmethod
    def _transform_source(source: str, mappings: t.StrMapping) -> str:
        """Transform source through the public class-nesting API."""
        transformer = FlextInfraRefactorClassNestingTransformer(mappings, {}, {})
        transformed, _ = transformer.apply_to_source(source)
        return transformed

    def test_project_processes_without_errors(self) -> None:
        """Verify multiple mapped classes are nested in one transformation."""
        source = "class TimeoutEnforcer:\n    pass\n\nclass RateLimiter:\n    pass\n"

        transformed = self._transform_source(
            source,
            {"TimeoutEnforcer": "FlextDispatcher", "RateLimiter": "FlextDispatcher"},
        )

        tm.that(transformed, ne=source)
        tm.that(transformed, has="class FlextDispatcher:")
        tm.that(transformed, has="    class TimeoutEnforcer:")
        tm.that(transformed, has="    class RateLimiter:")

    def test_no_type_errors_introduced(self) -> None:
        """Verify nesting preserves the class method type annotation."""
        source = (
            "from typing import Optional\n\n"
            "class Helper:\n"
            "    def process(self, x: Optional[int] = None) -> int:\n"
            "        return x or 0\n"
        )

        transformed = self._transform_source(source, {"Helper": "FlextUtilities"})

        tm.that(transformed, has="class FlextUtilities:")
        tm.that(transformed, has="x: Optional[int] = None")
