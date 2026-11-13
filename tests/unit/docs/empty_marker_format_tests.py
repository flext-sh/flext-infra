"""Generated empty-value markers agree with the markdown-format gate.

The generator and the formatter each own half of one text: a marker the
generator writes must already be the emphasis the formatter demands, or
``make gen`` and ``make fmt`` rewrite each other forever.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config
from flext_infra.gates import FlextInfraGatesMarkdownFormat
from tests import c, t, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDocsEmptyMarkerFormat:
    """An empty or undeclared value renders as formatter-stable Markdown."""

    @staticmethod
    @c.Tests.MARK.parametrize("language", ["en", "pt-BR"])
    @c.Tests.MARK.parametrize(
        "marker",
        [
            c.Infra.DocumentationText.NONE,
            c.Infra.DocumentationText.NOT_DECLARED,
        ],
    )
    def test_marker_is_a_markdown_format_fixed_point(
        tmp_path: Path,
        marker: c.Infra.DocumentationText,
        language: t.Infra.DocumentationLanguage,
    ) -> None:
        """The formatter leaves the generated marker untouched."""
        rules = u.Infra.markdown_native_configuration(
            config.Infra.tooling.tools.markdown,
            config.Infra.codegen.markdown_exclude_globs,
        )
        project = u.Tests.mk_project(tmp_path, "marker", markdown_config=rules)
        (project / "README.md").write_text(
            "# Marker\n\n- Public extensions exposed by this project: "
            f"{marker.localized(language)}.\n",
            encoding="utf-8",
        )
        _ = u.Tests.check_gate_asserting(
            FlextInfraGatesMarkdownFormat,
            tmp_path,
            project,
            passed=True,
            issues_len=0,
        )
