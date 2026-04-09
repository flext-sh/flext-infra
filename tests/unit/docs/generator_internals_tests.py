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


class TestGeneratorHelpers:
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
