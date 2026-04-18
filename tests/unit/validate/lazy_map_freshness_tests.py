"""Tests for FlextInfraValidateLazyMapFreshness.

Guard 2/3: stale-lazy-map detector. Thin wrapper over the existing
ROPE-backed lazy-init generator in check-only mode; the
generator's own unit tests cover the detailed stale-detection
semantics.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraValidateLazyMapFreshness
from tests import m, t


@pytest.fixture
def v() -> FlextInfraValidateLazyMapFreshness:
    """Shared validator instance."""
    return FlextInfraValidateLazyMapFreshness()


class TestLazyMapFreshnessValidatorCore:
    """Wrapper semantics: runs the check-only generator and formats the report."""

    def test_empty_workspace_yields_passing_report(
        self,
        tmp_path: Path,
        v: FlextInfraValidateLazyMapFreshness,
    ) -> None:
        report = tm.ok(v.build_report(tmp_path))
        assert isinstance(report, m.Infra.ValidationReport)
        tm.that(report.passed, eq=True)
        tm.that(report.violations, length=0)

    def test_passing_summary_mentions_lazy_maps(
        self,
        tmp_path: Path,
        v: FlextInfraValidateLazyMapFreshness,
    ) -> None:
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.summary, has="lazy")

    def test_report_is_validation_report(
        self,
        tmp_path: Path,
        v: FlextInfraValidateLazyMapFreshness,
    ) -> None:
        report = tm.ok(v.build_report(tmp_path))
        assert isinstance(report, m.Infra.ValidationReport)


__all__: t.StrSequence = []
