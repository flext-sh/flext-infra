"""Tests for FlextInfraReportingService — path types.

Tests cover return type validation for report path methods.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from tests import u


class TestFlextInfraReportingServiceExtra:
    """Test suite for FlextInfraReportingService extra operations."""

    @pytest.fixture
    def service(self) -> u.Infra:
        """Create a reporting service instance."""
        return u.Infra()

    def test_get_report_dir_returns_path(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        """Test that get_report_dir returns Path type."""
        result = service.get_report_dir(tmp_path, "project", "check")
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_get_report_path_returns_path(
        self,
        service: u.Infra,
        tmp_path: Path,
    ) -> None:
        """Test that get_report_path returns Path type."""
        result = service.get_report_path(tmp_path, "project", "check", "report.json")
        assert isinstance(result, Path)
        assert result.is_absolute()
