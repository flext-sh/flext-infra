"""Contracts for the accepted focused cProfile report renderer.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
from typing import TYPE_CHECKING

from flext_infra import config
from flext_infra.validate.cprofile_report import FlextInfraCProfileReport
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraCProfileReport:
    """Validate the standalone typed cProfile artifact renderer."""

    def test_execute_renders_a_bounded_readable_report(self, tmp_path: Path) -> None:
        """Render config-selected rows from a real standard-library profile."""
        report_dir = tmp_path / ".reports" / "tests" / "profile"
        report_dir.mkdir(parents=True)
        profile_path = report_dir / "profile.pstats"
        output_path = report_dir / "profile.txt"
        profiler = cProfile.Profile()
        profiler.runcall(sum, (1, 2, 3))
        profiler.dump_stats(profile_path)
        policy = config.Infra.tooling.tools.pytest

        tm.ok(
            FlextInfraCProfileReport(
                workspace=tmp_path,
                profile=profile_path,
                output=output_path,
                sort=policy.profile_sort,
                limit=policy.profile_limit,
            ).execute()
        )

        tm.that(output_path.read_text(encoding="utf-8"), has="function calls")
