"""Tests for FlextInfraReportingService — path types.

Tests cover return type validation for report path methods.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import u


class TestsFlextInfraInfraReportingExtra:
    """Test suite for FlextInfraReportingService extra operations."""

    @pytest.fixture
    def service(self) -> type[u.Cli]:
        """Create a reporting service instance."""
        service_cls: type[u.Cli] = u.Cli
        return service_cls

    def test_resolve_report_dir_returns_path(
        self,
        service: type[u.Cli],
        tmp_path: Path,
    ) -> None:
        """Test that resolve_report_dir returns Path type."""
        result = service.resolve_report_dir(tmp_path, "project", "check")
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_resolve_report_path_returns_path(
        self,
        service: type[u.Cli],
        tmp_path: Path,
    ) -> None:
        """Test that resolve_report_path returns Path type."""
        result = service.resolve_report_path(
            tmp_path, "project", "check", "report.json"
        )
        assert isinstance(result, Path)
        assert result.is_absolute()
