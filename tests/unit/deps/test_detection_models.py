"""Test detection models behavior.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import m, t
from flext_infra.deps.detection import FlextInfraDependencyDetectionService
from tests import tm


class TestsFlextInfraDepsDetectionModels:
    """Test flext infra deps detection models behavior."""

    @staticmethod
    def test_deptry_issue_groups_creation() -> None:
        """Verify deptry issue groups creation."""
        groups = m.Infra.DeptryIssueGroups()
        tm.that(groups.dep001, eq=[])
        tm.that(groups.dep002, eq=[])
        tm.that(groups.dep003, eq=[])
        tm.that(groups.dep004, eq=[])

    @staticmethod
    def test_deptry_report_creation() -> None:
        """Verify deptry report creation."""
        report = m.Infra.DeptryReport(
            missing=[],
            unused=[],
            transitive=[],
            dev_in_runtime=[],
            raw_count=0,
        )
        tm.that(report.missing, empty=True)
        tm.that(report.unused, empty=True)
        tm.that(report.transitive, empty=True)
        tm.that(report.dev_in_runtime, empty=True)
        tm.that(report.raw_count, eq=0)

    @staticmethod
    def test_project_dependency_report_creation() -> None:
        """Verify project dependency report creation."""
        deptry = m.Infra.DeptryReport(
            missing=[],
            unused=[],
            transitive=[],
            dev_in_runtime=[],
            raw_count=0,
        )
        report = m.Infra.ProjectDependencyReport(project="test-project", deptry=deptry)
        tm.that(report.project, eq="test-project")
        tm.that(report.deptry, eq=deptry)

    @staticmethod
    def test_service_initialization() -> None:
        """Verify service initialization."""
        FlextInfraDependencyDetectionService()

    @staticmethod
    def test_unsupported_type(tmp_path: Path) -> None:
        """Verify unsupported type."""
        with pytest.raises(m.ValidationError):
            _ = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(str(tmp_path))
