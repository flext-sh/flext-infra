"""Tests for FlextInfraTierWhitelistGate.

The gate must surface every abstraction-boundary violation the detector found.
Collapsing them into one aggregate issue pinned to the repository root makes
the gate unactionable and aggregates independent defects, which ``fail loud``
forbids.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tf, tm

from flext_infra.gates.tier_whitelist import FlextInfraTierWhitelistGate
from tests import m, u

if TYPE_CHECKING:
    from pathlib import Path


def _run_gate(project_dir: Path) -> m.Infra.GateResult:
    """Execute the gate against ``project_dir`` and return its result."""
    ctx = m.Infra.GateContext(
        repository_root=project_dir, reports_dir=project_dir / ".reports"
    )
    execution = FlextInfraTierWhitelistGate(repository_root=project_dir).check(
        project_dir, ctx
    )
    return execution.result


class TestTierWhitelistGateReporting:
    """Each violation reaches the report as its own issue."""

    def test_clean_project_passes_without_errors(self, tmp_path: Path) -> None:
        pkg = u.Tests.write_package_init(tmp_path / "src" / "pkg", "").parent
        tf(base_dir=pkg).create("from flext_core import m\nX = m.BaseModel\n", "ok.py")
        result = _run_gate(tmp_path)
        tm.that(result.passed, eq=True)
        tm.that(len(result.errors), eq=0)

    def test_every_violation_is_reported_individually(self, tmp_path: Path) -> None:
        # Three distinct offending modules must yield three errors, never one
        # aggregate count: the operator needs the offending file per entry.
        pkg = u.Tests.write_package_init(tmp_path / "src" / "pkg", "").parent
        files = tf(base_dir=pkg)
        files.create("from pydantic import BaseModel\n", "one.py")
        files.create("import structlog\n", "two.py")
        files.create("from returns.result import Result\n", "three.py")
        result = _run_gate(tmp_path)
        tm.that(result.passed, eq=False)
        tm.that(len(result.errors), eq=3)
        joined = " | ".join(result.errors)
        for offender in ("one.py", "two.py", "three.py"):
            tm.that(joined, has=offender)

    def test_error_count_is_not_a_summary_string(self, tmp_path: Path) -> None:
        # Guards the regression this gate carried: execute() returns a bool and
        # the summary "N violation(s)", so the gate emitted a single error that
        # named no file at all.
        pkg = u.Tests.write_package_init(tmp_path / "src" / "pkg", "").parent
        files = tf(base_dir=pkg)
        files.create("from pydantic import BaseModel\n", "a.py")
        files.create("import structlog\n", "b.py")
        result = _run_gate(tmp_path)
        tm.that(len(result.errors), eq=2)
        tm.that(" | ".join(result.errors), lacks="violation(s)")
