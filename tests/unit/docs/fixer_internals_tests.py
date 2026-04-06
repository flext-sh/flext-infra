"""Tests for FlextInfraDocFixer — internal methods: _process_file, TOC.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tf, tm
from tests import m, u

from flext_infra import FlextInfraDocFixer


@pytest.fixture
def fixer() -> FlextInfraDocFixer:
    return FlextInfraDocFixer()


class TestFixerProcessFile:
    @pytest.mark.parametrize(
        ("name", "content", "apply"),
        [
            ("test.md", "# Test\n\n[Link](missing.md)\n", False),
            ("test.md", "# Test\n\n## Section\n", True),
            ("test.md", "# Test\n\nNo broken links or TOC needed.", False),
        ],
    )
    def test_process_file_variants(
        self,
        fixer: FlextInfraDocFixer,
        tmp_path: Path,
        name: str,
        content: str,
        apply: bool,
    ) -> None:
        md_file = tf.create_in(content, name, tmp_path)
        item = fixer._process_file(md_file, apply=apply)
        tm.that(item.file, eq=str(md_file))

    def test_process_file_with_fixable_links(
        self,
        fixer: FlextInfraDocFixer,
        tmp_path: Path,
    ) -> None:
        md_file = tf.create_in("# Test\n\n[Link](target.md)\n", "test.md", tmp_path)
        _ = tf.create_in("# Target", "target.md", tmp_path)
        item = fixer._process_file(md_file, apply=False)
        tm.that(item.file, has="test.md")

    def test_fix_markdown_with_link_fix(
        self,
        fixer: FlextInfraDocFixer,
        tmp_path: Path,
    ) -> None:
        _ = tf.create_in("", "target.md", tmp_path)
        md_file = tf.create_in(
            "# Test\n\nSee [link](target) for details.\n",
            "README.md",
            tmp_path,
        )
        item = fixer._process_file(md_file, apply=False)
        tm.that(item.links, eq=1)


class TestFixerToc:
    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            ("Hello World", "hello-world"),
            ("Test-Case", "test-case"),
            ("  Spaces  ", "spaces"),
            ("Hello! World?", "hello-world"),
            ("Test@#$%", "test"),
            ("", ""),
            ("!!!", ""),
        ],
    )
    def test_anchorize_cases(
        self,
        fixer: FlextInfraDocFixer,
        title: str,
        expected: str,
    ) -> None:
        _ = fixer
        tm.that(u.Infra.anchorize(title), eq=expected)

    def test_build_toc_variants(self, fixer: FlextInfraDocFixer) -> None:
        _ = fixer
        toc = u.Infra.build_toc(
            "# Main\n\n## Section 1\n\n### Subsection\n\n## Section 2\n",
        )
        tm.that(toc, has="<!-- TOC START -->")
        tm.that(toc, has="<!-- TOC END -->")
        tm.that(toc, has="Section 1")
        tm.that(
            u.Infra.build_toc("# Main\n\nNo sections here.\n"),
            has="No sections found",
        )

    def test_build_toc_skips_empty_anchors(self, fixer: FlextInfraDocFixer) -> None:
        _ = fixer
        toc = u.Infra.build_toc("## !!!\n\n## Valid Section\n")
        tm.that(toc, has="Valid Section")
        tm.that("!!!" not in toc, eq=True)


class TestFixerScope:
    def test_fix_scope_with_markdown_files(self, tmp_path: Path) -> None:
        fixer = FlextInfraDocFixer()
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        _ = tf.create_in("# Test\n\n## Section\n", "README.md", docs_dir)
        scope = m.Infra.DocScope(
            name="test",
            path=tmp_path,
            report_dir=tmp_path / "reports",
        )
        report = fixer._fix_scope(scope, apply=False)
        tm.that(report.scope, eq="test")
        tm.that(len(report.items), gte=0)
