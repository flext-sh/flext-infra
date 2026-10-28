"""Regression coverage for nested Mypy process deadlines.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time

from tests import c, tm, u


class TestsFlextInfraMypyDeadline:
    """Keep analysis and inner termination ahead of outer soft interruption."""

    @staticmethod
    def test_runner_reserves_the_complete_inner_supervisor_window() -> None:
        """The runner cannot soft-interrupt analysis or the child's kill grace."""
        limit = u.Infra.mypy_resource_limit()
        timeout = u.Infra.mypy_runner_timeout(limit)
        started = time.monotonic()
        deadline = u.Infra.mypy_runner_deadline(timeout)
        finished = time.monotonic()
        inner_window = limit.timeout_seconds + c.Infra.TIMEOUT_KILL_AFTER_SECONDS
        soft_boundary = (
            deadline.expires_at_monotonic - deadline.termination_grace_seconds
        )
        tm.that(
            started + inner_window <= soft_boundary <= finished + inner_window,
            eq=True,
        )
        tm.that(deadline.expires_at_monotonic <= finished + timeout, eq=True)
