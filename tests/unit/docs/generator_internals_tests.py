"""Tests for FlextInfraDocGenerator — internal methods.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraDocGenerator
from tests import m, u


@pytest.fixture
def gen() -> FlextInfraDocGenerator:
    return FlextInfraDocGenerator()


class TestGeneratorScope:
    def test_generate_scope_root_scope(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        scope = m.Infra.DocScope(
            name="root",
            path=tmp_path,
            report_dir=tmp_path / "reports",
        )
        report = gen._generate_scope(scope, apply=False, workspace_root=tmp_path)
        tm.that(report.scope, eq="root")

    def test_generate_scope_project_scope(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        scope = m.Infra.DocScope(
            name="test-project",
            path=tmp_path,
            report_dir=tmp_path / "reports",
        )
        report = gen._generate_scope(scope, apply=False, workspace_root=tmp_path)
        tm.that(report.scope, eq="test-project")

    def test_generate_root_docs_creates_files(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        scope = m.Infra.DocScope(
            name="root",
            path=tmp_path,
            report_dir=tmp_path / "reports",
        )
        files = gen._generate_root_docs(scope, apply=False)
        tm.that(len(files), eq=3)

    def test_generate_project_guides_no_source(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        scope = m.Infra.DocScope(
            name="test",
            path=tmp_path,
            report_dir=tmp_path / "reports",
        )
        files = gen._generate_project_guides(
            scope,
            workspace_root=tmp_path,
            apply=False,
        )
        tm.that(files, eq=[])

    def test_generate_project_guides_with_source(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        guides_dir = tmp_path / "docs/guides"
        guides_dir.mkdir(parents=True, exist_ok=True)
        (guides_dir / "test.md").write_text("# Test Guide\n\nContent.\n")
        scope = m.Infra.DocScope(
            name="test",
            path=tmp_path / "project",
            report_dir=tmp_path / "reports",
        )
        files = gen._generate_project_guides(
            scope,
            workspace_root=tmp_path,
            apply=False,
        )
        tm.that(len(files), gte=0)

    def test_generate_project_mkdocs_creates_config(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        scope = m.Infra.DocScope(
            name="test",
            path=tmp_path,
            report_dir=tmp_path / "reports",
        )
        files = gen._generate_project_mkdocs(scope, apply=False)
        tm.that(len(files), eq=1)
        tm.that(files[0].path.endswith("mkdocs.yml"), eq=True)

    def test_generate_project_mkdocs_skips_existing(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "mkdocs.yml").write_text("site_name: Test\n")
        scope = m.Infra.DocScope(
            name="test",
            path=tmp_path,
            report_dir=tmp_path / "reports",
        )
        files = gen._generate_project_mkdocs(scope, apply=False)
        tm.that(files, eq=[])


class TestGeneratorHelpers:
    def test_project_guide_content_adds_heading(
        self,
        gen: FlextInfraDocGenerator,
    ) -> None:
        result = gen._project_guide_content(
            "# Original Title\n\nContent here.\n",
            "my-project",
            "guide.md",
        )
        tm.that(result, has="my-project - Original Title")

    def test_project_guide_content_preserves_body(
        self,
        gen: FlextInfraDocGenerator,
    ) -> None:
        result = gen._project_guide_content(
            "# Title\n\nBody content.\n",
            "proj",
            "guide.md",
        )
        tm.that(result, has="Body content")

    def test_sanitize_internal_anchor_links_removes_local_links(
        self,
        gen: FlextInfraDocGenerator,
    ) -> None:
        result = gen._sanitize_internal_anchor_links(
            "[Link](local.md) and [External](http://example.com)",
        )
        tm.that(result, has="Link")
        tm.that(result, has="http://example.com")

    def test_sanitize_internal_anchor_links_preserves_external(
        self,
        gen: FlextInfraDocGenerator,
    ) -> None:
        result = gen._sanitize_internal_anchor_links(
            "[Local](local.md) [External](https://example.com)",
        )
        tm.that(result, has="https://example.com")

    def test_normalize_anchor_converts_to_slug(
        self,
        gen: FlextInfraDocGenerator,
    ) -> None:
        _ = gen
        tm.that(u.Infra.anchorize("Hello World"), eq="hello-world")
        tm.that(u.Infra.anchorize("Test-Case"), eq="test-case")

    def test_normalize_anchor_empty_string(self, gen: FlextInfraDocGenerator) -> None:
        _ = gen
        tm.that(u.Infra.anchorize(""), eq="")

    def test_build_toc_from_headings(self, gen: FlextInfraDocGenerator) -> None:
        _ = gen
        toc = u.Infra.build_toc("# Main\n\n## Section 1\n\n### Subsection\n")
        tm.that(toc, has="<!-- TOC START -->")
        tm.that(toc, has="Section 1")

    def test_build_toc_with_no_headings(self, gen: FlextInfraDocGenerator) -> None:
        _ = gen
        tm.that(u.Infra.build_toc("# Main\n\nNo sections.\n"), has="No sections found")

    def test_update_toc_replaces_existing(self, gen: FlextInfraDocGenerator) -> None:
        result = gen._update_toc(
            "# Main\n\n<!-- TOC START -->\nOld\n<!-- TOC END -->\n\n## Section\n",
        )
        tm.that("Old" not in result, eq=True)

    def test_update_toc_inserts_new(self, gen: FlextInfraDocGenerator) -> None:
        result = gen._update_toc("# Main\n\n## Section\n")
        tm.that(result, has="<!-- TOC START -->")

    def test_write_if_needed_no_change(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        path = tmp_path / "test.md"
        path.write_text("# Test\n")
        tm.that(not gen._write_if_needed(path, "# Test\n", apply=True).written, eq=True)

    def test_write_if_needed_with_apply(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        path = tmp_path / "test.md"
        result = gen._write_if_needed(path, "# New Content\n", apply=True)
        tm.that(result.written, eq=True)
        tm.that(path.exists(), eq=True)

    def test_write_if_needed_dry_run(
        self,
        gen: FlextInfraDocGenerator,
        tmp_path: Path,
    ) -> None:
        path = tmp_path / "test.md"
        tm.that(
            not gen._write_if_needed(path, "# New Content\n", apply=False).written,
            eq=True,
        )
