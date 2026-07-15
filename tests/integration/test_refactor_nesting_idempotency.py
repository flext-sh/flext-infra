"""Idempotency tests for class nesting transformation.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_tests import tm

from flext_infra.transformers.class_nesting import (
    FlextInfraRefactorClassNestingTransformer,
)


class TestsFlextInfraIntegrationRefactorNestingIdempotency:
    """Test that repeated class-nesting transformations are idempotent."""

    _SOURCE: str = "class TimeoutEnforcer:\n    pass\n"

    @staticmethod
    def _transform_source(source: str) -> str:
        """Transform source through the public class-nesting API."""
        transformer = FlextInfraRefactorClassNestingTransformer(
            {"TimeoutEnforcer": "FlextDispatcher"}, {}, {}
        )
        transformed, _ = transformer.apply_to_source(source)
        return transformed

    def test_first_run_produces_changes(self) -> None:
        """Verify the first transformation nests the loose class."""
        transformed = self._transform_source(self._SOURCE)

        tm.that(transformed, ne=self._SOURCE)
        tm.that(transformed, has="class FlextDispatcher:")
        tm.that(transformed, has="    class TimeoutEnforcer:")

    def test_second_run_produces_no_changes(self) -> None:
        """Verify a second transformation preserves the transformed source."""
        first = self._transform_source(self._SOURCE)
        second = self._transform_source(first)

        tm.that(second, eq=first)

    def test_third_run_produces_no_changes(self) -> None:
        """Verify idempotency remains stable across three transformations."""
        transformed = self._SOURCE
        for _ in range(3):
            previous = transformed
            transformed = self._transform_source(transformed)
        tm.that(transformed, eq=previous)
