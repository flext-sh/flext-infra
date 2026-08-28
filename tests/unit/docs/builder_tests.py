"""Tests for FlextInfraDocBuilder — core build and scope tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra.docs.builder import FlextInfraDocBuilder
from flext_tests import tm
from tests import m

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


@pytest.fixture
def builder() -> FlextInfraDocBuilder:
    """Provide the public documentation builder service."""
    return FlextInfraDocBuilder()


class TestBuilderCore:
    """Core build invocation tests."""

    def test_build_with_valid_scope_returns_success(
        self, builder: FlextInfraDocBuilder, tmp_path: Path
    ) -> None:
        """Test build with valid scope returns success."""
        reports: t.SequenceOf[m.Infra.DocsPhaseReport] = tm.ok(builder.build(tmp_path))
        tm.that(len(reports), gte=0)

    def test_build_report_frozen(self) -> None:
        """Test BuildReport is frozen (immutable)."""
        tm.that(m.Infra.DocsPhaseReport.model_config.get("frozen"), eq=True)

    def test_build_with_custom_output_dir(
        self, builder: FlextInfraDocBuilder, tmp_path: Path
    ) -> None:
        """Build accepts an explicit report destination."""
        tm.ok(builder.build(tmp_path, output_dir=tmp_path / "custom_output"))

    @pytest.mark.parametrize("status", ["OK", "FAIL", "SKIP"])
    def test_build_report_result_field_values(
        self, status: str, tmp_path: Path
    ) -> None:
        """Test BuildReport result field accepts valid values."""
        report = m.Infra.DocsPhaseReport(
            phase="build",
            scope="test",
            result=status,
            reason="Test reason",
            site_dir=str(tmp_path / "site"),
        )
        tm.that(report.result, eq=status)

    def test_build_report_site_dir_field(self) -> None:
        """Test BuildReport site_dir field."""
        report = m.Infra.DocsPhaseReport(
            phase="build",
            scope="test",
            result="OK",
            reason="Build successful",
            site_dir="/path/to/site",
        )
        tm.that(report.site_dir, eq="/path/to/site")
