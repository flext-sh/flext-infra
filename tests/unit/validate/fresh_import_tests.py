"""Tests for FlextInfraValidateFreshImport.

Guard 7: fresh-process import smoke test — imports each advertised package
in a subprocess and fails when any raises ImportError. Catches cycles
lazy-loading would mask.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest
from flext_tests import tm

from flext_infra import FlextInfraValidateFreshImport
from tests import m, t


@pytest.fixture
def v() -> FlextInfraValidateFreshImport:
    """Shared validator instance."""
    return FlextInfraValidateFreshImport()


class TestFreshImportValidatorCore:
    """Core validation: clean imports vs broken imports."""

    def test_empty_package_list_passes(
        self,
        v: FlextInfraValidateFreshImport,
    ) -> None:
        report = tm.ok(v.build_report(packages=()))
        assert isinstance(report, m.Infra.ValidationReport)
        tm.that(report.passed, eq=True)
        tm.that(report.violations, length=0)

    def test_stdlib_package_passes(
        self,
        v: FlextInfraValidateFreshImport,
    ) -> None:
        report = tm.ok(v.build_report(packages=("sys",)))
        tm.that(report.passed, eq=True)
        tm.that(report.violations, length=0)

    def test_nonexistent_package_fails(
        self,
        v: FlextInfraValidateFreshImport,
    ) -> None:
        report = tm.ok(
            v.build_report(packages=("nonexistent_pkg_xyz_abc_123",))
        )
        tm.that(report.passed, eq=False)
        tm.that(report.violations, length=1)
        tm.that(report.violations[0], has="nonexistent_pkg_xyz_abc_123")

    def test_mixed_good_and_bad_reports_only_bad(
        self,
        v: FlextInfraValidateFreshImport,
    ) -> None:
        report = tm.ok(
            v.build_report(packages=("sys", "nonexistent_xyz_qqq", "os"))
        )
        tm.that(report.passed, eq=False)
        tm.that(report.violations, length=1)
        tm.that(report.violations[0], has="nonexistent_xyz_qqq")

    def test_summary_reports_failure_count(
        self,
        v: FlextInfraValidateFreshImport,
    ) -> None:
        report = tm.ok(
            v.build_report(
                packages=("nonexistent_a_qqq", "nonexistent_b_qqq"),
            )
        )
        tm.that(report.summary, has="2")
        tm.that(report.summary, has="failed")

    def test_passing_summary_is_human_readable(
        self,
        v: FlextInfraValidateFreshImport,
    ) -> None:
        report = tm.ok(v.build_report(packages=("sys", "os")))
        tm.that(report.summary, has="import")


class TestFreshImportValidatorFlextPackages:
    """Smoke: core flext packages must import cleanly."""

    def test_flext_core_imports_cleanly(
        self,
        v: FlextInfraValidateFreshImport,
    ) -> None:
        report = tm.ok(v.build_report(packages=("flext_core",)))
        assert report.passed, report.summary

    def test_flext_infra_imports_cleanly(
        self,
        v: FlextInfraValidateFreshImport,
    ) -> None:
        report = tm.ok(v.build_report(packages=("flext_infra",)))
        assert report.passed, report.summary


__all__: t.StrSequence = []
