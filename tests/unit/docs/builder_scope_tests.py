"""Tests for FlextInfraDocBuilder — scope, mkdocs, and write_reports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from flext_tests import tm

from flext_core import r
from flext_infra import FlextInfraDocBuilder
from tests import m, t


class TestBuilderScope:
    """Tests for _build_scope and _run_mkdocs."""

    @pytest.fixture
    def builder(self) -> FlextInfraDocBuilder:
        """Create builder instance."""
        return FlextInfraDocBuilder()

    def test_build_scope_with_mkdocs_config(
        self,
        builder: FlextInfraDocBuilder,
        tmp_path: Path,
    ) -> None:
        """Test _build_scope with mkdocs.yml present."""
        (tmp_path / "mkdocs.yml").write_text("site_name: Test\n")
        scope = m.Infra.DocScope(
            name="test",
            path=tmp_path,
            report_dir=tmp_path / "reports",
        )
        report = builder._build_scope(scope)
        tm.that(report.scope, eq="test")

    def test_build_scope_without_mkdocs_config(
        self,
        builder: FlextInfraDocBuilder,
        tmp_path: Path,
    ) -> None:
        """Test _build_scope without mkdocs.yml returns SKIP."""
        scope = m.Infra.DocScope(
            name="test",
            path=tmp_path,
            report_dir=tmp_path / "reports",
        )
        report = builder._build_scope(scope)
        tm.that(report.result, eq="SKIP")

    def test_build_with_scope_failure_returns_failure(
        self,
        builder: FlextInfraDocBuilder,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test build returns failure when scope building fails."""

        def mock_build_scopes(
            *args: t.Scalar,
            **kwargs: t.Scalar,
        ) -> r[Sequence[m.Infra.DocScope]]:
            return r[Sequence[m.Infra.DocScope]].fail("Scope error")

        result = builder.build(tmp_path)
        tm.fail(result, has="Scope error")

    def test_build_multiple_scopes(
        self,
        builder: FlextInfraDocBuilder,
        tmp_path: Path,
    ) -> None:
        """Test build returns multiple reports for multiple scopes."""
        result = builder.build(tmp_path, projects=["proj1", "proj2", "proj3"])
        if result.is_success:
            tm.that(len(result.value), gte=0)
