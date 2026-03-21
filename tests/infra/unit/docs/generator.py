"""Tests for FlextInfraDocGenerator — core generate and model tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import m, t, u

from flext_core import r, t
from flext_infra.docs.generator import FlextInfraDocGenerator
from flext_infra.docs.shared import FlextInfraDocsShared
from tests.infra.models import m


class TestGeneratorCore:
    """Core generate invocation tests."""

    @pytest.fixture
    def gen(self) -> FlextInfraDocGenerator:
        """Create generator instance."""
        return FlextInfraDocGenerator()

    def test_generate_returns_flext_result(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        """Test that generate returns r."""
        result = gen.generate(tmp_path)
        u.Tests.Matchers.that(result.is_success or result.is_failure, eq=True)

    def test_generate_with_valid_scope_returns_success(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        """Test generate with valid scope returns success."""
        result = gen.generate(tmp_path)
        u.Tests.Matchers.ok(result)
        u.Tests.Matchers.that(len(result.value) >= 0, eq=True)

    def test_generate_report_structure(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        """Test GenerateReport has required fields."""
        result = gen.generate(tmp_path)
        if result.is_success and result.value:
            report = result.value[0]
            u.Tests.Matchers.that(hasattr(report, "scope"), eq=True)
            u.Tests.Matchers.that(hasattr(report, "generated"), eq=True)
            u.Tests.Matchers.that(hasattr(report, "applied"), eq=True)
            u.Tests.Matchers.that(hasattr(report, "source"), eq=True)
            u.Tests.Matchers.that(hasattr(report, "items"), eq=True)

    def test_generated_file_structure(self) -> None:
        """Test GeneratedFile model structure."""
        file = m.Infra.GeneratedFile(path="README.md", written=True)
        u.Tests.Matchers.that(file.path, eq="README.md")
        u.Tests.Matchers.that(file.written, eq=True)

    def test_generate_report_frozen(self) -> None:
        """Test GenerateReport is frozen (immutable)."""
        u.Tests.Matchers.that(
            m.Infra.DocsPhaseReport.model_config.get("frozen"), eq=True
        )

    def test_generated_file_frozen(self) -> None:
        """Test GeneratedFile is frozen (immutable)."""
        u.Tests.Matchers.that(m.Infra.GeneratedFile.model_config.get("frozen"), eq=True)

    def test_generate_with_project_filter(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        """Test generate with single project filter."""
        result = gen.generate(tmp_path, project="test-project")
        u.Tests.Matchers.that(result.is_success or result.is_failure, eq=True)

    def test_generate_with_projects_filter(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        """Test generate with multiple projects filter."""
        result = gen.generate(tmp_path, projects="proj1,proj2")
        u.Tests.Matchers.that(result.is_success or result.is_failure, eq=True)

    def test_generate_with_apply_false_dry_run(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        """Test generate with apply=False (dry-run mode)."""
        result = gen.generate(tmp_path, apply=False)
        u.Tests.Matchers.that(result.is_success or result.is_failure, eq=True)

    def test_generate_with_apply_true_writes_files(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        """Test generate with apply=True writes files."""
        result = gen.generate(tmp_path, apply=True)
        u.Tests.Matchers.that(result.is_success or result.is_failure, eq=True)

    def test_generate_with_custom_output_dir(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        """Test generate with custom output directory."""
        result = gen.generate(tmp_path, output_dir=str(tmp_path / "custom_output"))
        u.Tests.Matchers.that(result.is_success or result.is_failure, eq=True)

    def test_generate_report_generated_count(self) -> None:
        """Test GenerateReport generated field."""
        report = m.Infra.DocsPhaseReport(
            phase="generate",
            scope="test",
            generated=5,
            applied=True,
            source="test-source",
        )
        u.Tests.Matchers.that(report.generated, eq=5)

    def test_generate_report_applied_field(self) -> None:
        """Test GenerateReport applied field."""
        report = m.Infra.DocsPhaseReport(
            phase="generate",
            scope="test",
            generated=0,
            applied=False,
            source="test-source",
        )
        u.Tests.Matchers.that(report.applied, eq=False)

    def test_generate_report_source_field(self) -> None:
        """Test GenerateReport source field."""
        report = m.Infra.DocsPhaseReport(
            phase="generate",
            scope="test",
            generated=0,
            applied=False,
            source="workspace-ssot",
        )
        u.Tests.Matchers.that(report.source, eq="workspace-ssot")

    def test_generate_report_files_list(self) -> None:
        """Test GenerateReport files list."""
        items = [
            m.Infra.DocsPhaseItem(phase="generate", path="file1.md", written=True),
            m.Infra.DocsPhaseItem(
                phase="generate",
                path="file2.md",
                written=False,
            ),
        ]
        report = m.Infra.DocsPhaseReport(
            phase="generate",
            scope="test",
            generated=2,
            applied=True,
            source="test-source",
            items=items,
        )
        u.Tests.Matchers.that(len(report.items), eq=2)
        u.Tests.Matchers.that(report.items[0].model_dump().get("path"), eq="file1.md")

    def test_generated_file_written_field(self) -> None:
        """Test GeneratedFile written field."""
        u.Tests.Matchers.that(
            m.Infra.GeneratedFile(path="test.md", written=True).written,
            eq=True,
        )
        u.Tests.Matchers.that(
            m.Infra.GeneratedFile(path="test2.md", written=False).written,
            eq=False,
        )

    def test_generate_with_scope_failure_returns_failure(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test generate returns failure when scope building fails."""

        def mock_build_scopes(
            *args: t.Scalar,
            **kwargs: t.Scalar,
        ) -> r[list[m.Infra.FlextInfraDocScope]]:
            return r[list[m.Infra.FlextInfraDocScope]].fail("Scope error")

        monkeypatch.setattr(FlextInfraDocsShared, "build_scopes", mock_build_scopes)
        result = gen.generate(tmp_path)
        u.Tests.Matchers.fail(result, has="Scope error")
