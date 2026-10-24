"""Test detector models behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from tests import m, tm


class TestsFlextInfraDepsDetectorModels:
    """Test flext infra deps detector models behavior."""

    @staticmethod
    def test_pip_check_report_creation() -> None:
        """Verify pip check report creation."""
        report = m.Infra.PipCheckReport(ok=True, lines=[])
        tm.ok(report.ok)
        tm.that(report.lines, empty=True)

    @staticmethod
    def test_workspace_dependency_report_creation() -> None:
        """Verify workspace dependency report creation."""
        report = m.Infra.WorkspaceDependencyReport.model_validate({
            "workspace": "test-workspace",
            "projects": {},
        })
        tm.that(report.workspace, eq="test-workspace")
        tm.that(report.projects, empty=True)
        tm.that(report.pip_check, eq=None)
