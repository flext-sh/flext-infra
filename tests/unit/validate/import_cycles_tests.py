"""Tests for FlextInfraValidateImportCycles.

Guard 1: ROPE-backed AST cycle detector. Builds a module import graph
via rope's import resolution and runs Tarjan's SCC; any SCC of size >= 2
is a cycle violation. TYPE_CHECKING imports are excluded by rope's
semantic parser because they live in conditional blocks.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tf, tm

from flext_infra import FlextInfraValidateImportCycles
from tests import m, t


@pytest.fixture
def v() -> FlextInfraValidateImportCycles:
    """Shared validator instance."""
    return FlextInfraValidateImportCycles()


def _seed_pkg(root: Path, name: str = "pkg") -> Path:
    pkg = root / "src" / name
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    return pkg


class TestImportCyclesValidatorCore:
    """Cycle detection: passes clean trees, flags cycles."""

    def test_empty_workspace_passes(
        self,
        tmp_path: Path,
        v: FlextInfraValidateImportCycles,
    ) -> None:
        report = tm.ok(v.build_report(tmp_path))
        assert isinstance(report, m.Infra.ValidationReport)
        tm.that(report.passed, eq=True)

    def test_acyclic_graph_passes(
        self,
        tmp_path: Path,
        v: FlextInfraValidateImportCycles,
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf.create_in("X = 1\n", "a.py", pkg)
        tf.create_in("from pkg.a import X\n", "b.py", pkg)
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.passed, eq=True)

    def test_two_module_cycle_fails(
        self,
        tmp_path: Path,
        v: FlextInfraValidateImportCycles,
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf.create_in("from pkg import b\n", "a.py", pkg)
        tf.create_in("from pkg import a\n", "b.py", pkg)
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.passed, eq=False)
        joined = " | ".join(report.violations)
        tm.that(joined, has="pkg.a")
        tm.that(joined, has="pkg.b")

    def test_three_module_cycle_fails(
        self,
        tmp_path: Path,
        v: FlextInfraValidateImportCycles,
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf.create_in("from pkg import b\n", "a.py", pkg)
        tf.create_in("from pkg import c\n", "b.py", pkg)
        tf.create_in("from pkg import a\n", "c.py", pkg)
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.passed, eq=False)
        joined = " | ".join(report.violations)
        tm.that(joined, has="pkg.a")
        tm.that(joined, has="pkg.b")
        tm.that(joined, has="pkg.c")

    def test_type_checking_import_is_not_runtime_cycle(
        self,
        tmp_path: Path,
        v: FlextInfraValidateImportCycles,
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf.create_in(
            (
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n"
                "    from pkg import b\n"
            ),
            "a.py",
            pkg,
        )
        tf.create_in(
            "from pkg import a\n",
            "b.py",
            pkg,
        )
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.passed, eq=True)


class TestImportCyclesValidatorSummary:
    """Summary content: human-readable cycle descriptions."""

    def test_summary_reports_cycle_count(
        self,
        tmp_path: Path,
        v: FlextInfraValidateImportCycles,
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf.create_in("from pkg import b\n", "a.py", pkg)
        tf.create_in("from pkg import a\n", "b.py", pkg)
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.summary, has="1")
        tm.that(report.summary, has="cycle")

    def test_passing_summary_is_human_readable(
        self,
        tmp_path: Path,
        v: FlextInfraValidateImportCycles,
    ) -> None:
        _seed_pkg(tmp_path)
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.summary, has="cycle")


__all__: t.StrSequence = []
