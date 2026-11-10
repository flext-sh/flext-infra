"""The public test runner does not depend on quality-check execution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import tm, u


class TestsFlextInfraPytestCheckIndependence:
    """Exercise a real suite without a checker receipt or checker invocation."""

    @staticmethod
    def test_full_suite_executes_without_a_check_receipt(
        cached_runner_project: Path,
    ) -> None:
        """A fresh consumer executes and reports its actual test population."""
        root = cached_runner_project
        runner = u.Tests.PytestRunner.runner_for(root)
        tm.that(tm.ok(runner.execute_full()), eq=0)
        tm.that(u.Tests.PytestRunner.summary(root / runner.reports), has="executed=1")
