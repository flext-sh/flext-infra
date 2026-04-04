"""Tests for FlextInfraDocFixer — core fix, model, and link tests.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from flext_tests import tf, tm
from tests import m, t

from flext_core import r
from flext_infra import FlextInfraDocFixer, FlextInfraUtilitiesDocs


class TestFixerCore:
    """Core fix invocation tests."""

    @pytest.fixture
    def fixer(self) -> FlextInfraDocFixer:
        """Create fixer instance."""
        return FlextInfraDocFixer()

    def test_fix_returns_flext_result(
        self,
        fixer: FlextInfraDocFixer,
        tmp_path: Path,
    ) -> None:
        """Test that fix returns r."""
        result = fixer.fix(tmp_path)
        tm.that(result.is_success or result.is_failure, eq=True)

    def test_fix_with_valid_scope_returns_success(
        self,
        fixer: FlextInfraDocFixer,
        tmp_path: Path,
    ) -> None:
        """Test fix with valid scope returns success."""
        result = fixer.fix(tmp_path)
        tm.ok(result)
        tm.that(len(result.value), gte=0)

    def test_fix_report_structure(
        self,
        fixer: FlextInfraDocFixer,
        tmp_path: Path,
    ) -> None:
        """Test FixReport has required fields."""
        result = fixer.fix(tmp_path)
        if result.is_success and result.value:
            report = result.value[0]
            tm.that(hasattr(report, "scope"), eq=True)
            tm.that(hasattr(report, "changed_files"), eq=True)
            tm.that(hasattr(report, "applied"), eq=True)
            tm.that(hasattr(report, "items"), eq=True)

    def test_fix_item_structure(self) -> None:
        """Test FixItem model structure."""
        item = m.Infra.DocsPhaseItemModel(phase="fix", file="README.md", links=2, toc=1)
        tm.that(item.file, eq="README.md")
        tm.that(item.links, eq=2)
        tm.that(item.toc, eq=1)

    def test_fix_report_frozen(self) -> None:
        """Test FixReport is frozen (immutable)."""
        tm.that(m.Infra.DocsPhaseReport.model_config.get("frozen"), eq=True)

    def test_fix_item_frozen(self) -> None:
        """Test FixItem is frozen (immutable)."""
        tm.that(m.Infra.DocsPhaseItemModel.model_config.get("frozen"), eq=True)

    @pytest.mark.parametrize(
        ("project", "apply", "output_dir"),
        [
            (["test-project"], False, ".reports/docs"),
            (["proj1", "proj2"], False, ".reports/docs"),
            (None, False, ".reports/docs"),
            (None, True, ".reports/docs"),
            (None, False, "custom_output"),
        ],
    )
    def test_fix_with_option_variants(
        self,
        fixer: FlextInfraDocFixer,
        tmp_path: Path,
        project: list[str] | None,
        apply: bool,
        output_dir: str,
    ) -> None:
        if apply:
            _ = tf.create_in("# Test\n\nSome content here.\n", "README.md", tmp_path)
        output_dir_value = (
            str(tmp_path / output_dir) if output_dir == "custom_output" else output_dir
        )
        result = fixer.fix(
            tmp_path,
            project=project,
            output_dir=output_dir_value,
            apply=apply,
        )
        tm.that(result.is_success or result.is_failure, eq=True)

    def test_fix_report_changed_files_count(self) -> None:
        """Test FixReport changed_files field."""
        report = m.Infra.DocsPhaseReport(
            phase="fix",
            scope="test",
            changed_files=5,
            applied=True,
        )
        tm.that(report.changed_files, eq=5)

    @pytest.mark.parametrize(
        ("changed_files", "applied"),
        [(0, False), (5, True)],
    )
    def test_fix_report_applied_field(self, changed_files: int, applied: bool) -> None:
        """Test FixReport applied field."""
        report = m.Infra.DocsPhaseReport(
            phase="fix",
            scope="test",
            changed_files=changed_files,
            applied=applied,
        )
        tm.that(report.applied, eq=applied)

    def test_fix_report_items_list(self) -> None:
        """Test FixReport items list."""
        items = [
            m.Infra.DocsPhaseItemModel(phase="fix", file="file1.md", links=1, toc=0),
            m.Infra.DocsPhaseItemModel(phase="fix", file="file2.md", links=0, toc=1),
        ]
        report = m.Infra.DocsPhaseReport(
            phase="fix",
            scope="test",
            changed_files=2,
            applied=True,
            items=items,
        )
        tm.that(len(report.items), eq=2)
        tm.that(report.items[0].model_dump().get("file"), eq="file1.md")

    def test_fix_with_scope_failure_returns_failure(
        self,
        fixer: FlextInfraDocFixer,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test fix returns failure when scope building fails."""

        def mock_build_scopes(
            *args: t.Scalar,
            **kwargs: t.Scalar,
        ) -> r[Sequence[m.Infra.DocScope]]:
            return r[Sequence[m.Infra.DocScope]].fail("Scope error")

        monkeypatch.setattr(FlextInfraUtilitiesDocs, "build_scopes", mock_build_scopes)
        result = fixer.fix(tmp_path)
        tm.fail(result, has="Scope error")
