"""Verify the CI global incremental run leaves slow items out of the fast tier.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraPytestRunnerFastCi:
    """Operator decision 2026-11-22: CI runs the fast tests only."""

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("ci_context", "mode", "expected"),
        [
            (True, c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL, False),
            (False, c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL, True),
            (True, c.Infra.PytestExecutionMode.FULL, True),
            (False, c.Infra.PytestExecutionMode.FULL, True),
            (True, c.Infra.PytestExecutionMode.COVERAGE, True),
            (True, c.Infra.PytestExecutionMode.INCREMENTAL, False),
        ],
    )
    def test_slow_items_are_carried_except_by_the_ci_fast_tier(
        cached_runner_project: Path,
        *,
        ci_context: bool,
        mode: c.Infra.PytestExecutionMode,
        expected: bool,
    ) -> None:
        """Only the CI global incremental run drops slow items."""
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, ci_context=ci_context
        )
        tm.that(runner.carries_slow_items(mode), eq=expected)
