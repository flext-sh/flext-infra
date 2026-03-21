"""Tests for FlextInfraReportingService — report dir/path operations.

Tests cover report path generation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import u


class TestFlextInfraReportingServiceCore:
    """Test suite for FlextInfraReportingService core operations."""

    @pytest.fixture
    def service(self) -> u.Infra:
        """Create a reporting service instance."""
        return u.Infra()

    def test_get_report_dir_project_scope(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        """Test getting project-level report directory."""
        result = service.get_report_dir(tmp_path, "project", "check")
        assert isinstance(result, Path)
        assert result.name == "check"
        assert ".reports" in str(result)
        assert "workspace" not in str(result)

    def test_get_report_dir_workspace_scope(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        """Test getting workspace-level report directory."""
        result = service.get_report_dir(tmp_path, "workspace", "validate")
        assert isinstance(result, Path)
        assert result.name == "validate"
        assert ".reports" in str(result)
        assert "workspace" in str(result)

    def test_get_report_dir_with_string_root(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        """Test getting report directory with string root path."""
        result = service.get_report_dir(str(tmp_path), "project", "test")
        assert isinstance(result, Path)
        assert result.name == "test"

    def test_get_report_path_project_scope(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        """Test getting project-level report file path."""
        result = service.get_report_path(tmp_path, "project", "check", "report.json")
        assert isinstance(result, Path)
        assert result.name == "report.json"
        assert ".reports" in str(result)
        assert "check" in str(result)

    def test_get_report_path_workspace_scope(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        """Test getting workspace-level report file path."""
        result = service.get_report_path(
            tmp_path,
            "workspace",
            "validate",
            "summary.log",
        )
        assert isinstance(result, Path)
        assert result.name == "summary.log"
        assert ".reports" in str(result)
        assert "workspace" in str(result)
        assert "validate" in str(result)

    def test_get_report_path_with_string_root(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        """Test getting report file path with string root."""
        result = service.get_report_path(
            str(tmp_path),
            "project",
            "test",
            "results.xml",
        )
        assert isinstance(result, Path)
        assert result.name == "results.xml"
