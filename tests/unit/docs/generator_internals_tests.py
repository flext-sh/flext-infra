"""Public utility tests used by docs generation flows."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.docs.generator import FlextInfraDocGenerator
from tests import m, u


def test_anchorize_normalizes_headings() -> None:
    tm.that(u.Infra.anchorize("Hello World"), eq="hello-world")
    tm.that(u.Infra.anchorize("Test-Case"), eq="test-case")
    tm.that(u.Infra.anchorize(""), eq="")


def test_build_toc_lists_h2_and_h3_sections() -> None:
    toc = u.Infra.build_toc("# Main\n\n## Section 1\n\n### Subsection\n")

    tm.that(toc, has="<!-- TOC START -->")
    tm.that(toc, has="Section 1")
    tm.that(toc, has="Subsection")


def test_update_toc_replaces_existing_block() -> None:
    updated, changed = u.Infra.update_toc(
        "# Main\n\n<!-- TOC START -->\n- stale\n<!-- TOC END -->\n\n## Section\n"
    )

    tm.that(changed, eq=1)
    tm.that(updated, lacks="stale")
    tm.that(updated, has="Section")


def test_generate_creates_selected_project_reports(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(
        tmp_path, project_names=("flext-a", "flext-b")
    )

    result = FlextInfraDocGenerator().generate(
        m.Infra.DocsGenerateRequest(
            workspace_root=workspace, projects=["flext-a"], apply=True
        )
    )

    tm.ok(result)
    tm.that([report.scope for report in result.value], eq=["root", "flext-a"])
