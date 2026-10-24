"""Tests for FlextInfraValidateFreshImport.

Guard 7: fresh-process import smoke test — imports each advertised package
in a subprocess and fails when any raises ImportError. Catches cycles
lazy-loading would mask.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra.validate import FlextInfraValidateFreshImport
from tests import m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraFreshImport:
    """Fresh-process import smoke test suite."""

    @staticmethod
    @pytest.fixture
    def v() -> FlextInfraValidateFreshImport:
        """Shared validator instance.

        Returns:
            The resulting ``FlextInfraValidateFreshImport``.

        """
        return FlextInfraValidateFreshImport()

    @staticmethod
    def test_probes_run_in_the_declared_target_environment(
        tmp_path: Path,
    ) -> None:
        """The declared target interpreter runs the probes, not the tool's.

        The tool's environment imports flext_core; the declared target's fresh
        stdlib environment does not, so the probe must fail there.
        """
        # The target is a real checkout: its own Git root owns the runtime.
        u.Tests.initialize_git_repo(tmp_path)
        u.Tests.provision_runtime_environment(tmp_path)
        validator = FlextInfraValidateFreshImport(
            repository_root=tmp_path,
            runtime_root=tmp_path,
        )
        report = tm.ok(validator.build_report(packages=("flext_core",)))
        tm.fail(report.passed)
        tm.that(report.violations[0], has="No module named 'flext_core'")

    @staticmethod
    def test_declared_target_without_interpreter_fails_loudly(
        tmp_path: Path,
    ) -> None:
        """A declared target lacking its interpreter fails, never falls back.

        The runtime proves the environment is physical before probing its
        interpreter, so the case declares a physical environment without one.
        """
        u.Infra.runtime_environment_dir(tmp_path, runtime_root=tmp_path).mkdir()
        validator = FlextInfraValidateFreshImport(
            repository_root=tmp_path,
            runtime_root=tmp_path,
        )
        result = validator.build_report(packages=("sys",))
        tm.fail(result, has="fresh-import target interpreter is missing")

    @staticmethod
    def test_empty_package_list_passes(v: FlextInfraValidateFreshImport) -> None:
        """Test empty package list passes."""
        report: m.Infra.ValidationReport = tm.ok(v.build_report(packages=()))
        tm.that(report, is_=m.Infra.ValidationReport)
        tm.ok(report.passed)
        tm.that(report.violations, length=0)

    @staticmethod
    def test_stdlib_package_passes(v: FlextInfraValidateFreshImport) -> None:
        """Test stdlib package passes."""
        report: m.Infra.ValidationReport = tm.ok(v.build_report(packages=("sys",)))
        tm.ok(report.passed)
        tm.that(report.violations, length=0)

    @staticmethod
    def test_nonexistent_package_fails(v: FlextInfraValidateFreshImport) -> None:
        """Test nonexistent package fails."""
        report: m.Infra.ValidationReport = tm.ok(
            v.build_report(packages=("nonexistent_pkg_xyz_abc_123",)),
        )
        tm.fail(report.passed)
        tm.that(report.violations, length=1)
        tm.that(report.violations[0], has="nonexistent_pkg_xyz_abc_123")

    @staticmethod
    def test_mixed_good_and_bad_reports_only_bad(
        v: FlextInfraValidateFreshImport,
    ) -> None:
        """Test mixed good and bad reports only bad."""
        report: m.Infra.ValidationReport = tm.ok(
            v.build_report(packages=("sys", "nonexistent_xyz_qqq", "os")),
        )
        tm.fail(report.passed)
        tm.that(report.violations, length=1)
        tm.that(report.violations[0], has="nonexistent_xyz_qqq")

    @staticmethod
    def test_stops_at_first_causal_failure(
        v: FlextInfraValidateFreshImport,
    ) -> None:
        """Test stops at first causal failure."""
        report: m.Infra.ValidationReport = tm.ok(
            v.build_report(packages=("nonexistent_a_qqq", "nonexistent_b_qqq")),
        )
        tm.that(report.violations, length=1)
        tm.that(report.violations[0], has="nonexistent_a_qqq")
        tm.that(report.violations[0], lacks="nonexistent_b_qqq")
        tm.that(report.summary, has="failed")

    @staticmethod
    def test_passing_summary_is_human_readable(
        v: FlextInfraValidateFreshImport,
    ) -> None:
        """Test passing summary is human readable."""
        report: m.Infra.ValidationReport = tm.ok(v.build_report(packages=("sys", "os")))
        tm.that(report.summary, has="import")

    @staticmethod
    def test_workspace_src_package_passes(
        tmp_path: Path,
        suite_runtime_root: Path,
    ) -> None:
        """A checkout's src package imports in its declared runtime."""
        package_root = tmp_path / "src" / "demo_external"
        package_root.mkdir(parents=True)
        package_root.joinpath("__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
        validator = FlextInfraValidateFreshImport(
            repository_root=tmp_path,
            runtime_root=suite_runtime_root,
        )
        report: m.Infra.ValidationReport = tm.ok(
            validator.build_report(packages=("demo_external",)),
        )
        tm.that(report.passed, eq=True, msg=str(report.violations))

    @staticmethod
    def test_flext_core_imports_cleanly(v: FlextInfraValidateFreshImport) -> None:
        """Test flext core imports cleanly."""
        report: m.Infra.ValidationReport = tm.ok(
            v.build_report(packages=("flext_core",)),
        )
        tm.that(report.passed, eq=True, msg=report.summary)

    @staticmethod
    def test_flext_infra_imports_cleanly(
        v: FlextInfraValidateFreshImport,
    ) -> None:
        """Test flext infra imports cleanly."""
        report: m.Infra.ValidationReport = tm.ok(
            v.build_report(packages=("flext_infra",)),
        )
        tm.that(report.passed, eq=True, msg=report.summary)
